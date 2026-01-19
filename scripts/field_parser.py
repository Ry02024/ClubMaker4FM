"""
field_parser.py - ユーザー入力からフィールド名を抽出するパーサー

このモジュールはユーザーの自由形式入力から純粋なフィールド名のみを抽出します。
括弧内の説明、不要な単語、重複を除去し、クリーンなリストを返します。
"""

import re
from typing import List


def parse_field_names(raw_input: str) -> List[str]:
    """
    ユーザー入力からフィールド名を抽出する
    
    例:
        入力: "dp / dp2（伝票）\nreceipt（領収書）\npay / pay_attrs / pay_kubun（支払い関連）"
        出力: ["dp", "dp2", "receipt", "pay", "pay_attrs", "pay_kubun"]
    
    Args:
        raw_input: ユーザーの自由形式テキスト
    
    Returns:
        クリーンなフィールド名のリスト
    """
    if not raw_input:
        return []
    
    # Step 1: 全角括弧とその中身を削除 （...）
    text = re.sub(r'（[^）]*）', '', raw_input)
    
    # Step 2: 半角括弧とその中身を削除 (...)
    text = re.sub(r'\([^)]*\)', '', text)
    
    # Step 3: カテゴリ名を削除してフィールドリストのみを残す
    # 「システム構造: app / crms_app」→「app / crms_app」
    # 全角コロン「：」と半角コロン「:」の両方に対応
    lines = text.split('\n')
    processed_lines = []
    for line in lines:
        # コロンがある場合、コロンより後ろの部分のみを抽出
        if '：' in line:
            line = line.split('：', 1)[1]  # 最初のコロンで分割、後ろを取得
        elif ':' in line:
            line = line.split(':', 1)[1]
        processed_lines.append(line)
    text = '\n'.join(processed_lines)
    
    # Step 3.5: 不要な単語・フレーズを削除
    noise_patterns = [
        r'など',
        r'等',
        r'【[^】]*】',  # 【...】を削除
        r'\[[^\]]*\]',  # [...]を削除
    ]
    for pattern in noise_patterns:
        text = re.sub(pattern, '', text, flags=re.MULTILINE)
    
    # Step 3.5: 指示文っぽい行を除外（ください、お願い、して、作成、以下、全てなどを含む）
    instruction_keywords = [
        'ください', 'お願い', '作成', 'して', '以下', '全て', 
        '設計', '生成', '追加', 'フィールドに', 'テーブルに',
        '項目を', 'を作って', '入れて', '基本的', 'そのまま',
        'これで', '既に'
    ]
    
    # Step 4: 区切り文字で分割 (/, ,, 改行, スペース)
    # 先に改行で分割
    lines = text.split('\n')
    
    field_names = []
    for line in lines:
        # 各行を / と , で分割
        parts = re.split(r'[/,]', line)
        for part in parts:
            # 空白をトリム
            name = part.strip()
            
            # 空文字、または無効な文字のみの場合はスキップ
            if not name:
                continue
            
            # 指示文っぽいテキストをスキップ
            is_instruction = any(kw in name for kw in instruction_keywords)
            if is_instruction:
                continue
            
            # 日本語のみの説明文っぽいものはスキップ（ただし日本語フィールド名は許可）
            # フィールド名として短すぎるもの（1文字未満）はスキップ
            if len(name) < 1:
                continue
            
            # 明らかに説明文（長すぎる日本語テキスト）はスキップ
            # ただし var_settings など英数字+アンダースコアは許可
            if len(name) > 30 and not re.match(r'^[a-zA-Z0-9_]+$', name):
                continue
            
            # 追加の空白除去（全角スペースも）
            name = name.replace('　', '').strip()
            
            if name:
                field_names.append(name)
    
    # Step 5: 重複排除（順序を維持）
    seen = set()
    unique_fields = []
    for name in field_names:
        if name not in seen:
            seen.add(name)
            unique_fields.append(name)
    
    return unique_fields


def extract_table_name(raw_input: str) -> str:
    """
    入力からテーブル名を抽出（デフォルト: 'base'）
    
    例:
        "baseテーブルに以下を作成" -> "base"
        "dpテーブル: ..." -> "dp"
    """
    # テーブル名を探すパターン
    patterns = [
        r'(\w+)テーブル',
        r'table[:\s]+(\w+)',
        r'(\w+)\s*table',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, raw_input, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return 'base'  # デフォルト


if __name__ == "__main__":
    # テスト
    test_input = """
dp / dp2（伝票）
receipt（領収書）
tc（タイムチャージ）
pay / pay_attrs / pay_kubun（支払い関連）
order / order_sum（オーダー・売上集計）
sales_drpt / sales_mrpt（売上日報・月報）
incoming（入金）
outgoing（出金）
colls（売掛回収）
bills（請求書）
casts（キャスト名簿）
cast_drpt（キャスト日報）
score（成績）
simei（指名：本指名・場内指名などの統合）
hns（本指名）
jyn（場内指名）
dhn_cnt / dhn_pt（同伴回数・ポイント）
earnings / earnings_staff（給与・バック関連）
customers（会員・顧客）
company（会社・自社情報）
menus / menu_attrs / menu_kubun（商品・メニュー関連）
btl / btl_back / btlin / btlout（ボトル管理関連）
inve（在庫・インベントリ）
manager（担当者）
taku（卓・席）
fees（料金システム）
hourly（時間別人数表）
システム構造: app / crms_app / config / opensys / layouts
共通変数: var / var_00 / var_01 / var_tmp / var_lib / var_pw / var_settings / var_datetime / var_vlist
機能別変数: var_dp, var_tc, var_simei, var_order, var_btl, var_menu, var_cast, var_cast_drpt, var_customer, var_manager, var_hourly, var_goback など
フラグ: flg_cash / flg_card / flg_ukake / flg_deposit / flg_kyubiki / flg_simei
takumap（卓マップ）
mkb（マウスタッチ・キーボード関連）
TodayWork（当日の作業記録）
topcstmr（優良顧客）
予約・予定：基本的にはyoteiで既に（rsv_929292 / yotei_939393）はそのまま
log（ログ）
    """
    
    fields = parse_field_names(test_input)
    print(f"抽出されたフィールド数: {len(fields)}")
    print("フィールド一覧:")
    for i, f in enumerate(fields, 1):
        print(f"  {i}. {f}")
