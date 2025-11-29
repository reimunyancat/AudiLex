from api.models import Processing

def format_status_data(processing):
    """
    Processing 객체를 상태 응답 데이터로 변환
    """
    return {
        'id': processing.id,
        'title': processing.title,
        'youtube_link': processing.youtube_link,
        'audio_status': processing.download_status,
        'subtitle_status': processing.transcript_status,
        'translation_status': processing.translate_status,
        'pronounce_status': processing.ipa_status,
        'created_at': processing.created_at,
    }

def get_status_by_id(id):
    """
    특정 id의 Processing 상태 조회
    Returns: (data, error)
    """
    try:
        processing = Processing.objects.get(id=id)
        return format_status_data(processing), None
    except Processing.DoesNotExist:
        return None, 'Processing not found'

def get_all_statuses():
    """
    모든 Processing 상태 조회
    """
    processings = Processing.objects.all().order_by('-created_at')
    return [format_status_data(p) for p in processings]
