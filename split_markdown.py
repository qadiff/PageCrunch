#!/usr/bin/env python3

import os
import sys
import argparse
from pathlib import Path

def split_file(input_file, size_bytes, prefix, output_dir="."):
    """
    ファイルを指定されたサイズで分割する
    
    Args:
        input_file (str): 分割する入力ファイルのパス
        size_bytes (int): 分割サイズ（バイト単位）
        prefix (str): 出力ファイルの接頭辞
        output_dir (str): 出力ディレクトリ
    """
    # 入力ファイルを開く
    try:
        with open(input_file, 'rb') as f:
            # 読み込みバッファ
            buffer = f.read(size_bytes)
            part_num = 1
            
            # バッファがある限り繰り返す
            while buffer:
                # 出力ファイル名を生成
                output_path = os.path.join(output_dir, f"{prefix}{part_num:03d}.md")
                
                # 出力ファイルに書き込む
                with open(output_path, 'wb') as out_file:
                    out_file.write(buffer)
                
                print(f"作成: {output_path} ({len(buffer)} バイト)")
                
                # 次のチャンクを読み込む
                buffer = f.read(size_bytes)
                part_num += 1
                
        print(f"分割完了: {part_num-1} ファイルが作成されました")
        
    except Exception as e:
        print(f"エラー: {str(e)}", file=sys.stderr)
        sys.exit(1)

def parse_size(size_str):
    """
    サイズ文字列（例: '1m', '500k'）をバイト数に変換
    
    Args:
        size_str (str): サイズ文字列
        
    Returns:
        int: バイト数
    """
    size_str = size_str.lower()
    
    # 単位マッピング
    units = {
        'k': 1024,
        'm': 1024 * 1024,
        'g': 1024 * 1024 * 1024,
        'b': 1
    }
    
    # 単位がない場合はバイト単位と見なす
    if size_str.isdigit():
        return int(size_str)
    
    # 数値部分と単位部分を分離
    for unit, multiplier in units.items():
        if size_str.endswith(unit):
            try:
                number = float(size_str[:-1])
                return int(number * multiplier)
            except ValueError:
                raise ValueError(f"無効なサイズ形式: {size_str}")
    
    raise ValueError(f"無効なサイズ単位: {size_str}")

def main():
    # コマンドライン引数のパーサーを設定
    parser = argparse.ArgumentParser(
        description="Markdownファイルを指定されたサイズで分割します",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument('-i', '--input', 
                        required=True, 
                        help="分割する入力ファイル")
    
    parser.add_argument('-s', '--size', 
                        default="1m", 
                        help="分割サイズ（例: 500k, 1m, 2g）")
    
    parser.add_argument('-p', '--prefix', 
                        default="part_", 
                        help="出力ファイルの接頭辞")
    
    parser.add_argument('-o', '--output-dir', 
                        default=".", 
                        help="出力ディレクトリ")
    
    args = parser.parse_args()
    
    # 入力ファイルの存在を確認
    if not os.path.isfile(args.input):
        print(f"エラー: ファイル '{args.input}' が見つかりません", file=sys.stderr)
        sys.exit(1)
    
    # 出力ディレクトリの存在を確認し、なければ作成
    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        try:
            output_dir.mkdir(parents=True)
            print(f"ディレクトリを作成しました: {output_dir}")
        except Exception as e:
            print(f"エラー: 出力ディレクトリを作成できません: {str(e)}", file=sys.stderr)
            sys.exit(1)
    
    # サイズをバイト数に変換
    try:
        size_bytes = parse_size(args.size)
    except ValueError as e:
        print(f"エラー: {str(e)}", file=sys.stderr)
        sys.exit(1)
    
    print(f"入力ファイル: {args.input}")
    print(f"分割サイズ: {args.size} ({size_bytes} バイト)")
    print(f"出力ファイル接頭辞: {args.prefix}")
    print(f"出力ディレクトリ: {args.output_dir}")
    
    # ファイル分割を実行
    split_file(args.input, size_bytes, args.prefix, args.output_dir)

if __name__ == "__main__":
    main()
