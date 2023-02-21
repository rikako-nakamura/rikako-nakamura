#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import glob
import os
import re
import subprocess


class CommandExecutor():
    def __init__(self, command, expect=None):
        self.command = command
        self.expects = []
        if expect:
            self.expects.append(expect)
        self.actuals = []

    def add_expect(self, expect):
        self.expects.append(expect)

    def execute(self) -> None:
        try:
            # コマンド実行
            output = subprocess.run(self.command, shell=True, text=True,
                                    capture_output=True, encoding='utf8')
            # エラー判定
            if err := output.stderr:
                self.actuals = err.splitlines()
                raise ValueError('Command error !')
            self.actuals = output.stdout.splitlines()
            # 結果判定
            assert self.expects == self.actuals
        except Exception as ex:
            raise ex

    def __repr__(self) -> str:
        if self.expects == self.actuals:
            text = '\033[0m'    # Black
            res = 'OK'
        else:
            text = '\033[91m'   # Red
            res = 'NG'
        text += f'    Command :  {self.command}\n'
        text += f'    Expect  :  {self.expects}\n'
        text += f'    Actual  :  {self.actuals}\n'
        text += f'    --> {res}\n'
        text += '\033[0m'           # Black
        return text


class TestCase():
    def __init__(self, file_path):
        self.err_msg = None

        # ソースコードを読み込む
        self.file_path = file_path
        if (not os.path.exists(file_path)):
            print(f'file does not exist. {file_path}')
        f = open(file_path, 'r', encoding='utf-8')
        txt = f.read()

        # コンパイル方法と実行例を抽出
        DIV_STR = '================\n'
        ptrn = f'.*?\n{DIV_STR}(.*?){DIV_STR}\n'
        self.command_sets = []
        for m in re.findall(ptrn, txt, re.DOTALL):
            for group in m.split(DIV_STR):
                command_sets = []
                for line in group.splitlines():
                    cmd = line.split('>>> ')
                    if len(cmd) > 1:
                        # 実行コマンド
                        command_sets.append(CommandExecutor(cmd[1]))
                    else:
                        # 期待する出力
                        command_sets[-1].add_expect(line)
                self.command_sets.append(command_sets)

    def execute(self):
        # 現在フォルダを保持して、作業フォルダに移動
        cwd = os.getcwd()
        os.chdir(os.path.dirname(self.file_path))

        try:
            # テストケースがない場合
            if not self.command_sets:
                self.err_msg = f'No test case'
                raise ValueError(self.err_msg)
            # テスト実行
            for command_set in self.command_sets:
                for command in command_set:
                    command.execute()
        except Exception as ex:
            self.err_msg = ex
            raise ex
        finally:
            # 元のディレクトリに戻る
            os.chdir(cwd)
            print(repr(self))

    def __repr__(self) -> str:
        text = '============================================================\n'
        text += f'{self.file_path}\n\n'
        for cnt, command_set in enumerate(self.command_sets):
            text += f'  No.{cnt}\n'
            for command in command_set:
                text += repr(command)
                text += '\n'
        return text


if __name__ == "__main__":

    # コマンドライン引数を取得
    parser = argparse.ArgumentParser()
    parser.add_argument('--keyword', default='')
    parser.add_argument('--terminate', default='0')
    args = parser.parse_args()
    keyword = args.keyword
    is_terminate = (args.terminate == '1')

    # テスト結果
    ok_cnt = 0
    ng_cnt = 0

    # テスト対象ファイル検索して、テスト実行
    file_paths = glob.glob(f'./**/src/*{keyword}*.c')
    file_paths.extend(glob.glob(f'./**/src/*{keyword}*.py'))
    file_paths.extend(glob.glob(f'./**/src/*{keyword}*.java'))
    for file_path in file_paths:
        try:
            TestCase(file_path).execute()
            ok_cnt += 1
        except Exception as ex:
            ng_cnt += 1
            # 途中終了フラグ
            if is_terminate:
                break

    # 結果出力
    print(f'============================================================\n')
    print(f'\t\t\tALL:{ok_cnt + ng_cnt:3}  OK:{ok_cnt:2}  NG:{ng_cnt:2}\n')
    print(f'============================================================\n')

    if ng_cnt > 0:
        exit(-1)
