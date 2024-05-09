import os
import datetime
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


def main():
    load_dotenv()
    # サービスアカウント鍵ファイルのパス
    SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE')

    # API スコープを設定
    SCOPES = ['https://www.googleapis.com/auth/drive']

    # サービスアカウントで認証
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    # Google Drive API クライアントを作成
    service = build('drive', 'v3', credentials=credentials)

    folder_id = os.getenv('FOLDER_ID')

    # 今日の日付が属するYYYYMMのフォルダ名を取得
    yyymm = datetime.datetime.now().strftime('%Y%m')
    # yymmでGoogle Driveのfoler_idに存在しなければフォルダを作成
    if not exists_folder(service, folder_id, yyymm):
        create_folder(service, folder_id, yyymm)

    query = f"'{folder_id}' in parents"
    results = service.files().list(q=query, pageSize=10, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print('ファイルが見つかりませんでした。')
    else:
        print('ファイルリスト:')
        for item in items:
            print(u'{0} ({1})'.format(item['name'], item['id']))


if __name__ == '__main__':
    main()
