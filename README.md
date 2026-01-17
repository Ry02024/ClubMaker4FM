# ClubMaker - AI-Driven FileMaker Architect

ClubMaker は、AI（Gemini 2.5 Flash）を活用して、FileMaker Pro のデータベース設計から画面制作までを劇的に効率化する開発支援ツールです。
「やりたいこと」を伝えるだけで、テーブル構造、フィールド定義、そしてモダンなレイアウトデザインまでをAIが提案し、実際の FileMaker へ自動反映します。

## 🚀 主な機能

### 1. AI データベース・デザイン
AIが要望を解析し、最適なテーブル名、フィールド名、データ型を設計します。設計の意図を確認できる「思考プロセス」機能も搭載しています。

### 2. 高信頼な GUI フィールド生成
pywinauto と pyautogui を組み合わせた高度な Windows 自動化により、FileMaker Pro の「データベースの管理」画面を直接操作してフィールドを作成します。
- **インテリジェント・レジューム**: 作成済みのフィールドを自動検知してスキップ。エラーで止まっても続きから再開可能。
- **入力ロック (BlockInput)**: 自動操作中のマウス・キーボード入力を物理的に遮断し、操作ミスを防止。
- **警告自動排除 (Modal Recovery)**: 名前重複や数式エラーなどの警告ダイアログを自動検知して排除。
- **計算フィールド完全対応**: 計算式の指定画面も自動でダミー入力を経て確定。

### 3. モダン・レイアウト生成 & XML連携
AIが設計したグリッドベースの画面レイアウトを XML 形式でコピーし、FileMaker のレイアウトモードへワンクリックで貼り付け可能です。
- **モダンなUIプレビュー**: ガラスモーフィズムやカードデザインを用いたプレビュー画面。
- **精密な座標計算**: AIの座標をポイント単位に自動変換して配置。

### 4. ブラウザ・オートメーション
FileMaker 本体の起動やウィンドウフォーカスの制御もAPI経由でサポートしています。

## 🛠 テクノロジースタック
- **Frontend**: Next.js 15 (App Router), Tailwind CSS
- **Backend API**: Next.js Route Handlers
- **Automation**: Python 3.10+ (pywinauto, pyautogui)
- **AI**: Google Generative AI (Gemini 2.0 Flash)

## 📦 セットアップ

### 1. 必要要件
- Windows 10/11
- FileMaker Pro 2024 (または Ver 19以降)
- Python 3.10 以上

### 2. 環境変数の設定
`.env` ファイルを作成し、以下の情報を設定してください。
```env
GOOGLE_GENERATIVE_AI_API_KEY=YOUR_API_KEY_1,YOUR_API_KEY_2
GOOGLE_GENERATIVE_AI_MODEL=gemini-2.0-flash-exp
```

### 3. インストール
```bash
# 依存関係のインストール
npm install

# Python 仮想環境の構築 (scripts実行に必要)
python -m venv .venv
.\.venv\Scripts\activate
pip install pywinauto pyautogui pyperclip google-generativeai
```

## 📖 使い方

1. **AI生成**: 画面上のプロンプトに要望を入力し「システムを生成する」をクリック。
2. **フィールド作成**: 設計を確認後、「一括GUI生成」をクリック。
   - ※実行前に FileMaker の「データベースの管理 > フィールド」タブを開いておいてください。
3. **レイアウト配置**: レイアウトタブで「レイアウトXMLをコピー」をクリックし、FileMaker のレイアウトモードで貼り付け。

## ⚠️ 注意事項
- 自動操作中は PC の操作（マウス・キーボード）を控えてください。
- 入力ロック機能をフルに活用するには、VS Code またはターミナルを「管理者として実行」することをお勧めします。

---
Created by Antigravity (Advanced Agentic Coding Agent)
