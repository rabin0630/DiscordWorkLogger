"""ログを新しい順にファイルへ書き、決まった行数を超えたら古い行を消すFileHandler"""
import logging
import os

class ReverseFileHandler(logging.FileHandler):
    def __init__(self, filename, mode='a', encoding=None, delay=False, max_lines=300):
        super().__init__(filename, mode='a', encoding=encoding, delay=delay)
        self.max_lines = max_lines
        
    def emit(self, record):
        try:
            msg = self.format(record)
            lines = []
            if os.path.exists(self.baseFilename):
                with open(self.baseFilename, 'r', encoding=self.encoding) as f:
                    lines = f.readlines()
            
            lines.insert(0, msg + '\n')
            if len(lines) > self.max_lines:
                lines = lines[:self.max_lines]
                
            with open(self.baseFilename, 'w', encoding=self.encoding) as f:
                f.writelines(lines)
        except Exception:
            self.handleError(record)

# ログの設定
logging.basicConfig(
    force = True,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        ReverseFileHandler("timer_bot.log", encoding="utf-8", max_lines=300), # 逆順かつ最大300行に制限
        logging.StreamHandler() # 今まで通りターミナル（画面）にも出す用
    ]
)