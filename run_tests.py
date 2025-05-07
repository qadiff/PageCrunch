#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PageCrunch のテスト実行スクリプト
"""

import unittest
import sys
import os
import coverage

# 現在のディレクトリをパスに追加
sys.path.insert(0, os.path.abspath('.'))

def run_tests_with_coverage():
    """
    単体テストを実行し、カバレッジレポートを生成
    """
    # カバレッジ測定を開始
    cov = coverage.Coverage(
        source=['page_crunch'],
        omit=['*/site-packages/*', '*/dist-packages/*', '*/__pycache__/*']
    )
    cov.start()
    
    # テストを探して実行
    loader = unittest.TestLoader()
    suite = loader.discover('.', pattern='test_*.py')
    
    # テスト結果をコンソールに表示
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # カバレッジ測定を終了し、レポートを表示
    cov.stop()
    cov.save()
    
    print('\nCoverage Summary:')
    cov.report()
    
    # HTMLレポートを生成
    cov.html_report(directory='htmlcov')
    print(f'HTML coverage report generated in htmlcov/ directory')
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests_with_coverage()
    sys.exit(0 if success else 1)
