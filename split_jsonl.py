#!/usr/bin/env python3
"""
JSONLファイルを指定したサイズで分割するスクリプト
"""
import os
import argparse
import json

def split_jsonl_file(input_file, output_prefix=None, max_size_mb=50):
    """
    JSONLファイルを指定したサイズ（MB）で複数のファイルに分割する

    # 出力プレフィックスを指定する場合
    python split_jsonl.py large_file.jsonl --output-prefix custom_prefix --max-size 50

    # 出力プレフィックスを省略する場合（入力ファイル名を使用）
    python split_jsonl.py large_file.jsonl --max-size 50
    
    Args:
        input_file (str): 入力JSONLファイルのパス
        output_prefix (str, optional): 出力ファイルのプレフィックス。指定がなければ入力ファイル名を使用
        max_size_mb (int): 出力ファイルの最大サイズ（MB）
    """
    # デフォルトのoutput_prefixを設定
    if output_prefix is None:
        # 入力ファイル名から拡張子を除いたものをプレフィックスとして使用
        output_prefix = os.path.splitext(os.path.basename(input_file))[0]
    
    # バイト単位での最大サイズに変換
    max_size_bytes = max_size_mb * 1024 * 1024
    
    file_index = 1
    current_size = 0
    output_file = f"{output_prefix}_{file_index}.jsonl"
    out_f = open(output_file, 'w', encoding='utf-8')
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                # 現在の行のサイズを取得（バイト単位）
                line_size = len(line.encode('utf-8'))
                
                # もし現在のファイルサイズ + 行のサイズが最大サイズを超える場合、新しいファイルを作成
                if current_size + line_size > max_size_bytes:
                    out_f.close()
                    print(f"Created {output_file} ({current_size / (1024 * 1024):.2f} MB)")
                    
                    # 新しいファイルを開く
                    file_index += 1
                    output_file = f"{output_prefix}_{file_index}.jsonl"
                    out_f = open(output_file, 'w', encoding='utf-8')
                    current_size = 0
                
                # 行を書き込み
                out_f.write(line)
                current_size += line_size
    
    finally:
        # 最後のファイルを閉じる
        if out_f:
            out_f.close()
            print(f"Created {output_file} ({current_size / (1024 * 1024):.2f} MB)")
    
    print(f"Split completed: {file_index} files created")

def main():
    parser = argparse.ArgumentParser(description='Split a JSONL file into smaller files')
    parser.add_argument('input_file', help='Input JSONL file')
    parser.add_argument('--output-prefix', help='Prefix for output files (default: input filename)')
    parser.add_argument('--max-size', type=int, default=50, help='Maximum size in MB for each output file (default: 50)')
    args = parser.parse_args()
    
    split_jsonl_file(args.input_file, args.output_prefix, args.max_size)

if __name__ == '__main__':
    main()
