from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from typing import Optional

def get_transcript(video_id: str) -> str:
    """
    動画IDから字幕を取得し、テキストとして返す。
    日本語 -> 自動翻訳日本語 の順に試行。
    取得できない場合はエラーを送出する。
    """
    try:
        # 字幕リストを取得
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)
        
        # 1. まず日本語の字幕(手動作成または自動生成)を探す
        try:
            transcript = transcript_list.find_transcript(['ja'])
        except NoTranscriptFound:
            # 2. 見つからない場合は、翻訳可能な字幕(例えば英語)を日本語に翻訳する
            try:
                # 英語などの他の字幕を取得し、日本語に翻訳
                # 取得可能な最初の字幕を翻訳対象にする
                first_available = list(transcript_list)[0]
                transcript = first_available.translate('ja')
            except Exception as e:
                raise ValueError("日本語への翻訳可能な字幕が見つかりませんでした。")
                
        # 字幕データを取得
        transcript_data = transcript.fetch()
        
        # クリーニング・整形 (TextFormatterを使用するとタイムスタンプなしのプレーンテキストになる)
        formatter = TextFormatter()
        text_transcript = formatter.format_transcript(transcript_data)
        
        # 簡易的なクリーニング（連続する改行を1つにするなど）
        # TextFormatterは各行を改行で結合する
        cleaned_text = "\n".join([line.strip() for line in text_transcript.split('\n') if line.strip()])
        
        if not cleaned_text:
             raise ValueError("字幕データは取得できましたが、内容が空でした。")
             
        return cleaned_text
        
    except TranscriptsDisabled:
        raise ValueError("この動画では字幕が無効になっています。")
    except NoTranscriptFound:
        raise ValueError("この動画には利用可能な字幕がありません。")
    except VideoUnavailable:
        raise ValueError("動画が利用できません（非公開か削除された可能性があります）。")
    except Exception as e:
        raise ValueError(f"字幕の取得中にエラーが発生しました: {str(e)}")


def get_transcript_with_timestamps(video_id: str) -> Optional[list]:
    """
    タイムスタンプ付きの字幕データをリスト形式で返す。
    各要素: {"start": 秒数(float), "text": "字幕テキスト"}
    AIによる重要シーン選定に使用する。
    取得できない場合は None を返す（エラーは握りつぶす）。
    """
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)
        
        try:
            transcript = transcript_list.find_transcript(['ja'])
        except NoTranscriptFound:
            first_available = list(transcript_list)[0]
            transcript = first_available.translate('ja')
        
        transcript_data = transcript.fetch()
        
        # タイムスタンプ付きリストに整形
        result = []
        for entry in transcript_data:
            # youtube-transcript-api v1.x は FetchedTranscriptSnippet オブジェクトを返す
            # .start, .text 属性でアクセス可能（dict-likeアクセスも対応）
            try:
                start = entry.start if hasattr(entry, 'start') else entry['start']
                text = entry.text if hasattr(entry, 'text') else entry['text']
            except (AttributeError, KeyError, TypeError):
                continue
            result.append({"start": float(start), "text": str(text).strip()})
        
        return result if result else None
        
    except Exception:
        return None
