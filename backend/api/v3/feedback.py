import json
from django.http import HttpResponse

from cms.models import Page, PageFeedback, PageTranslation


class FeedbackData:
    def __init__(self, page_id, permalink, comment, emotion):
        self.page_id = page_id
        self.permalink = permalink
        self.comment = comment
        self.emotion = emotion

    def from_dict(dict):
        return FeedbackData(
            dict.get('id', None),
            dict.get('permalink', None),
            dict.get('comment', None),
            dict.get('emotion', None)
        )

    def has_id(self):
        return self.__is_either_exist(self.page_id, self.permalink)

    def has_content(self):
        return self.__is_either_exist(self.comment, self.emotion)

    def get_comment(self):
        return self.comment if self.comment else ''

    def get_emotion(self):
        return self.emotion if self.emotion else "NA"

    def __is_either_exist(self, one, two):
        return one or two

def feedback(req, site_slug, languages):
    if req.method != 'POST':
        return HttpResponse(f'Invalid request method.', status=405)

    data = json.loads(req.body)
    feedback_data = FeedbackData.from_dict(data)

    if not feedback_data.has_id():
        return HttpResponse(f'No page found for site "{site_slug}" with permalink "{feedback_data.permalink}".',
                            content_type='text/plain', status=404)

    if not feedback_data.has_content():
        return HttpResponse("Please enter a valid rating/comment.", content_type='text/plain', status=400)

    page = Page.objects.get(id=feedback_data.page_id)
    if not page:
        page_translation = PageTranslation.objects.get(permalink=feedback_data.permalink)
        page = page_translation.page

    try:
        page_feedback = PageFeedback(page=page, emotion=feedback_data.get_emotion(),
                                     comment=feedback_data.get_comment())
        page_feedback.save()
        return HttpResponse(status=200)
    except ValueError:
        return HttpResponse("Bad request.", content_type='text/plain', status=400)
