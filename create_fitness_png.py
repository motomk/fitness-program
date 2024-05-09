import os
import datetime
import argparse
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build


def exists_folder(service, folder_id, folder_name):
    query = f"name = '{folder_name}' and '{folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
    results = service.files().list(q=query, spaces='drive', fields="files(id, name)").execute()
    return len(results.get('files', [])) > 0


def create_folder(service, parent_id, folder_name):
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    file = service.files().create(body=file_metadata, fields='id').execute()
    print(f"フォルダ '{folder_name}' を作成しました, ID: {file.get('id')}")


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


def main():
    load_dotenv()

    # オプションを確認
    parser = argparse.ArgumentParser(description='python create_fitness_png.py -c YYYYMM')
    parser.add_argument('-c', '--create', type=str, help='YYYYMMフォルダの画像を読み取ります', required=True)
    args = parser.parse_args()
    service = initialize_google_drive_service()
    folder_id = os.getenv('FOLDER_ID')

    # items = read_files(service, folder_id)

    # 今日の日付が属するYYYYMMのフォルダ名を取得
    yyymm = datetime.datetime.now().strftime('%Y%m')
    # yymmでGoogle Driveのfoler_idに存在しなければフォルダを作成
    if not exists_folder(service, folder_id, yyymm):
        create_folder(service, folder_id, yyymm)

    # オプション-cがあれば、オプションの値と同じフォルダのファイル一覧を取得
    if args.create:
        custom_folder = args.create
        custom_folder_id = get_folder_id_by_name(service, folder_id, custom_folder)
        if custom_folder_id:
            print(f'フォルダID {custom_folder_id} を取得しました。')
        print(f'指定されたフォルダ {custom_folder} のファイル一覧を取得します。')
        items = read_files(service, custom_folder_id)
        print(items)


if __name__ == '__main__':
    main()
