import os
import re
import io
import datetime
import argparse
import pytesseract
from PIL import Image
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


def exists_folder(service, folder_id, folder_name):
    query = f"name = '{folder_name}' and '{folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
    results = service.files().list(q=query, spaces='drive', fields="files(id, name)").execute()
    return len(results.get('files', [])) > 0


def initialize_google_drive_service():
    # サービスアカウント鍵ファイルのパス
    SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE')

    # API スコープを設定
    SCOPES = ['https://www.googleapis.com/auth/drive']

    # サービスアカウントで認証
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    # Google Drive API クライアントを作成
    service = build('drive', 'v3', credentials=credentials)
    return service


def read_files(service, folder_id):
    query = f"'{folder_id}' in parents"
    results = service.files().list(q=query, pageSize=10, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print('ファイルが見つかりませんでした。')
    else:
        print('ファイルリスト:')
        for item in items:
            print(u'{0} ({1})'.format(item['name'], item['id']))
    return items


def get_folder_id_by_name(service, parent_folder_id, folder_name):
    query = f"mimeType='application/vnd.google-apps.folder' and '{parent_folder_id}' in parents and name='{folder_name}'"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    folders = results.get('files', [])
    if folders:
        return folders[0]['id']
    else:
        print(f'フォルダ {folder_name} が見つかりませんでした。')
        return None


def create_sub_folder(service, folder_id):
    # 今日の日付が属するYYYYMMのフォルダ名を取得
    yyymm = datetime.datetime.now().strftime('%Y%m')
    # yyymmでGoogle Driveのfolder_idに存在しなければフォルダを作成
    if not exists_folder(service, folder_id, yyymm):
        file_metadata = {
            'name': yyymm,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [folder_id]
        }
        file = service.files().create(body=file_metadata, fields='id').execute()
        print(f"フォルダ '{yyymm}' を作成しました, ID: {file.get('id')}")


def main():
    load_dotenv()

    # オプションを確認
    parser = argparse.ArgumentParser(description='python create_fitness_png.py -c YYYYMM')
    parser.add_argument('-c', '--create', type=str, help='YYYYMMフォルダの画像を読み取ります', required=True)
    args = parser.parse_args()
    service = initialize_google_drive_service()
    folder_id = os.getenv('FOLDER_ID')

    # YYYYMMフォルダがなければ作成する
    create_sub_folder(service, folder_id)

    # オプション-cがあれば、オプションの値と同じフォルダのファイル一覧を取得
    if args.create:
        custom_folder = args.create
        custom_folder_id = get_folder_id_by_name(service, folder_id, custom_folder)
        if custom_folder_id:
            print(f'フォルダID {custom_folder_id} を取得しました。')
        print(f'指定されたフォルダ {custom_folder} のファイル一覧を取得します。')
        items = read_files(service, custom_folder_id)
        png_files = [item for item in items]
        if png_files:
            print(f'.pngファイルの数: {len(png_files)}')
            # ファイルを読み込んで日付がある部分を認識して変数に格納する
            date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}')

            file_date_info = []
            for file in png_files:
                # Google Driveからファイルをダウンロード
                request = service.files().get_media(fileId=file['id'])
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    fh.seek(0)
                # 画像ファイルを読み込む
                image = Image.open(fh)
                # OCRを使用してテキストを抽出
                text = pytesseract.image_to_string(image)

                # 日付を検索
                date_pattern = re.compile(r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}')
                dates = date_pattern.findall(text)
                # 日付形式を変換する
                converted_dates = []
                for date in dates:
                    # 元の形式は DD/MM/YYYY HH:MM なので、日付部分だけを取り出して変換
                    date_only = date.split(' ')[0]  # 'DD/MM/YYYY' を取得
                    day, month, year = date_only.split('/')
                    converted_date = f'{year}-{month}-{day}'
                    converted_dates.append(converted_date)
                # file['name'], file['id'], converted_dateの配列を保持するためのリストを初期化
                for date in converted_dates:
                    file_date_info.append({'name': file['name'], 'id': file['id'], 'date': date})
                # file_date_infoを日付順にソートして更新
                file_date_info = sorted(file_date_info, key=lambda x: x['date'])
        # 画像を合成するためのリストを初期化
        images_to_merge = []
        # 選択されたファイルから画像をダウンロードしてリストに追加
        for file_info in file_date_info:
            request = service.files().get_media(fileId=file_info['id'])
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                fh.seek(0)
            image = Image.open(fh)
            images_to_merge.append(image)
        # 画像を4列で合成する
        num_images = len(images_to_merge)
        print(f'num_images: {num_images}')
        num_columns = 4
        num_rows = (num_images + num_columns - 1) // num_columns  # 切り上げて行数を計算
        # 合成画像のサイズを計算（すべての画像は同じサイズと仮定）
        if num_images > 0:
            width, height = images_to_merge[0].size
            merged_width = width * num_columns
            merged_height = height * num_rows
            # 新しい画像を作成
            merged_image = Image.new('RGB', (merged_width, merged_height))
            # 画像を新しい画像に配置
            for index, image in enumerate(images_to_merge):
                x = (index % num_columns) * width
                y = (index // num_columns) * height
                merged_image.paste(image, (x, y))
            # 画像を保存
            output_filename = f'{args.create}.png'
            merged_image.save(output_filename)
            print(f'画像が保存されました: {output_filename}')


if __name__ == '__main__':
    main()
