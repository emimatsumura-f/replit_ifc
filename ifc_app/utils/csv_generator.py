import csv
from datetime import datetime

def generate_csv(elements, filepath):
    """
    要素情報をCSVファイルに出力する
    
    Args:
        elements (list): 部材情報のリスト
        filepath (str): 出力先のファイルパス
    """
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["部材種別", "部材名", "断面性能", "重量", "長さ"])
        for element in elements:
            writer.writerow([
                element["type"],
                element["name"],
                element["size"],
                element["weight"],
                element["length"]
            ])

def generate_csv_filename():
    """CSVファイルの名前を生成する"""
    return f"部材リスト_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
