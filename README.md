# Fitness PNG Creator

このプログラムは、Google Drive内の特定のフォルダからPNG画像を取得し、それらを処理して一つの画像にマージするPythonスクリプトです。OCRを使用して画像から日付情報を抽出し、その情報に基づいて画像を日付順に並べ替えてからマージします。

## 機能

- Google Drive APIを使用して特定のフォルダからPNG画像をダウンロード。
- ダウンロードした画像からOCRを用いてテキスト情報を抽出。
- 抽出したテキストから日付情報を検出し、それに基づいて画像をソート。
- ソートされた画像を一つの画像ファイルにマージして保存。

## 使用方法

1. `.env` ファイルに `SERVICE_ACCOUNT_FILE` と `FOLDER_ID` を設定します。
2. コマンドラインからスクリプトを実行します。

```
python create_fitness_png.py -c YYYYMM
```


## `.env` ファイルの設定

`.env` ファイルには以下の環境変数を設定する必要があります。

- `SERVICE_ACCOUNT_FILE`: サービスアカウントのJSON鍵ファイルへのパス。
- `FOLDER_ID`: 画像ファイルが保存されているGoogle DriveのフォルダID。

## 注意事項

- このスクリプトは、Google Driveのサービスアカウントを使用して認証を行います。
- OCR処理の精度は画像のクオリティに依存します。
- すべての画像が同じ解像度であることを前提としています。