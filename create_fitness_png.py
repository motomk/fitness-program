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
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload


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


def download_and_open_image(service, file_id):
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        fh.seek(0)
    return Image.open(fh)


def process_files(service, png_files, folder_id, output_prefix):
    for file in png_files:
        image = download_and_open_image(service, file['id'])
        # OCRを使用してテキストを抽出
        text = pytesseract.image_to_string(image)

        # 日付を検索
        date_pattern = re.compile(r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}')
        dates = date_pattern.findall(text)
        # 日付形式を変換する
        if dates:
            date = dates[0]
            # 元の形式は DD/MM/YYYY HH:MM なので、日付部分だけを取り出して変換
            date_only = date.split(' ')[0]  # 'DD/MM/YYYY' を取得
            day, month, year = date_only.split('/')
            converted_date = f'{year}{month}{day}'
        else:
            # 日付が見つからない場合、現在の日付を使用
            converted_date = datetime.datetime.now().strftime('%Y%m%d')

        # 画像をリネームして保存
        output_filename = f'{converted_date}_{output_prefix}.png'
        output_file_path = io.BytesIO()
        image.save(output_file_path, format='PNG')
        output_file_path.seek(0)

        # Google Driveに保存
        file_metadata = {
            'name': output_filename,
            'parents': [folder_id]
        }
        media = MediaIoBaseUpload(output_file_path, mimetype='image/png')
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print("画像がGoogle Driveに保存されました: " + output_filename + ", ID: " + file.get('id'))


def setup_and_parse_arguments():
    load_dotenv()
    parser = argparse.ArgumentParser(description='python create_fitness_png.py -c YYYYMM')
    parser.add_argument('-c', '--create', type=str, help='YYYYMMフォルダの画像を読み取ります', required=True)
    args = parser.parse_args()
    return args


def prepare_folder_and_files(service, folder_id, custom_folder):
    create_sub_folder(service, folder_id)
    custom_folder_id = get_folder_id_by_name(service, folder_id, custom_folder)
    if custom_folder_id:
        print(f'フォルダID {custom_folder_id} を取得しました。')
    print(f'指定されたフォルダ {custom_folder} のファイル一覧を取得します。')
    items = read_files(service, custom_folder_id)
    png_files = [item for item in items if item['name'].lower().endswith('.png')]
    return png_files, custom_folder_id


def main():
    args = setup_and_parse_arguments()
    service = initialize_google_drive_service()
    folder_id = os.getenv('FOLDER_ID')
    output_prefix = os.getenv('NAME')

    if args.create:
        png_files, custom_folder_id = prepare_folder_and_files(service, folder_id, args.create)
        if png_files:
            print(f'.pngファイルの数: {len(png_files)}')
            process_files(service, png_files, custom_folder_id, output_prefix)


if __name__ == '__main__':
    main()
