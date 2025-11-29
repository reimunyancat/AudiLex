from api.models import Audio


def format_status_data(audio):
    """Audio 객체를 상태 응답 데이터로 변환"""
    return {
        'id': str(audio.id),
        'youtube_link': audio.youtube_link,
        'youtube_title': getattr(audio, 'youtube_title', ''),
        'audio_status': audio.audio_status,
        'subtitle_status': audio.subtitle_status,
        'translation_status': audio.translation_status,
        'pronounce_status': audio.pronounce_status,
        'audio_dir': audio.audio_dir,
    }


def get_status_by_id(audio_id):
    """특정 id의 Audio 상태 조회"""
    try:
        audio = Audio.objects.get(pk=audio_id)
        return format_status_data(audio), None
    except Audio.DoesNotExist:
        return None, 'Audio not found'


def get_all_statuses():
    """모든 Audio 상태 조회"""
    return [format_status_data(audio) for audio in Audio.objects.all().order_by('-id')]
