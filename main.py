import os
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build


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

    # ここで Google Drive API を使用した操作を行う
    folder_id = os.getenv('FOLDER_ID')
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
