import json
from src.services.get_suumo_detail_urls import get_suumo_detail_urls
from src.services.get_suumo_scraper_detail import get_suumo_scraper_detail
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
from tqdm import tqdm
import src.services.constants as C
import os

def get_next_page_url(soup, current_url):
    """
    BeautifulSoupオブジェクトから「次へ」リンクのURLを取得する
    :param soup: BeautifulSoupオブジェクト
    :param current_url: 現在のページのURL
    :return: 次ページの絶対URL（存在しない場合はNone）
    """
    next_link = None
    for a in soup.select(C.PAGINATION_PARTS_SELECTOR):
        if a.text.strip() == C.NEXT_PAGE_TEXT:
            next_link = a
            break
    if next_link and next_link.has_attr('href'):
        return urljoin(current_url, next_link['href'])
    return None

def run_suumo_scraping(search_target_url):
    print("SUUMOスクレイピング開始...")
    
    all_detail_urls = []  # 全ページの詳細URLを格納するリスト
    page = 1  # 現在のページ番号
    current_url = search_target_url  # 現在処理中のページURL

    # ページ送りしながら全ページ分の詳細URLを取得
    while current_url:
        print(f"{page}ページ目を処理中...")
        response = requests.get(current_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        # 1ページ分の詳細URLを取得
        detail_urls = get_suumo_detail_urls(current_url)
        all_detail_urls.extend(detail_urls)
        print(f"{page}ページ目の物件数: {len(detail_urls)}件／合計: {len(all_detail_urls)}件")
        # 次ページのURLを取得
        next_url = get_next_page_url(soup, current_url)
        if not next_url:
            print("最終ページに到達しました")
            break
        current_url = next_url
        page += 1

    print(f"詳細URL合計: {len(all_detail_urls)}件")

    scraping_results = []  # 物件詳細データを格納するリスト
    # tqdmで進捗バーを表示しながら詳細ページを処理
    for idx, unit_url in enumerate(tqdm(all_detail_urls, desc="詳細ページ処理中"), 1):
        # 単体の詳細データを取得
        data = get_suumo_scraper_detail(unit_url)
        if data:
            scraping_results.append(data)
        # 10件ごとに進捗ログを出力
        if idx % 10 == 0 or idx == len(all_detail_urls):
            print(f"処理完了：{idx}件／全体: {len(all_detail_urls)}件")

    print("スクレイピング完了しました")
    # スクレイピング後のデータをログ出力
    # FIXME 最初の2件を出力   
    # print(json.dumps(scraping_results[:2], ensure_ascii=False, indent=2))

    # FIXME 結果をFrontディレクトリに保存
    # 保存先：frontend/public/static_data.json に変更（プロジェクトルート基準で解決）
    # プロジェクトルート（local_home_scraper）を絶対パスで取得
    abs_path = os.path.abspath(__file__)
    parts = abs_path.split(os.sep)
    if 'local_home_scraper' in parts:
        idx = parts.index('local_home_scraper')
        project_root = os.sep.join(parts[:idx+1])
    else:
        raise RuntimeError('local_home_scraper ディレクトリがパスに見つかりません')
    frontend_public_dir = os.path.join(project_root, 'frontend', 'public')
    os.makedirs(frontend_public_dir, exist_ok=True)
    output_path = os.path.join(frontend_public_dir, 'static_data.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(scraping_results, f, ensure_ascii=False, indent=2)
    print(f"スクレイピング結果を {output_path} に保存しました")

def main():
    """
    エントリーポイント
    """
    print("run suumo_scraper.py")
    search_target_url = C.DEFAULT_SEARCH_URL
    run_suumo_scraping(search_target_url)
if __name__ == "__main__":
    main()