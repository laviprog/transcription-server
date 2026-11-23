from typing import NotRequired

from whisperx.schema import SingleSegment


class Segment(SingleSegment):
    """
    A transcription segment as it leaves the pipeline: whisperx adds the ``speaker``
    key during diarization, so it is absent unless recognition mode was requested.
    """

    speaker: NotRequired[str]
