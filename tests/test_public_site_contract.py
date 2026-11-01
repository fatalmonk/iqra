from html.parser import HTMLParser
from pathlib import Path
import json
import subprocess
import unittest

ROOT = Path(__file__).parents[1]


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.en = []
        self.bn = []
        self.visible = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1
        for name, value in attrs:
            if name == "data-en" and value:
                self.en.append(value)
            elif name == "data-bn" and value:
                self.bn.append(value)

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.visible.append(data)


class SurveyParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.fieldsets = []
        self.current = None
        self.in_legend = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "fieldset":
            self.current = {"legend": [], "textarea": [], "choices": []}
            self.fieldsets.append(self.current)
        elif self.current is not None and tag == "legend":
            self.in_legend = True
        elif self.current is not None and tag == "textarea":
            self.current["textarea"].append(attrs.get("id", ""))
        elif self.current is not None and tag == "input" and attrs.get("type") == "checkbox":
            self.current["choices"].append(attrs.get("value", ""))

    def handle_endtag(self, tag):
        if tag == "legend":
            self.in_legend = False
        elif tag == "fieldset":
            self.current = None

    def handle_data(self, data):
        if self.current is not None and self.in_legend:
            self.current["legend"].append(data)

    def legend(self, fieldset):
        return " ".join(" ".join(fieldset["legend"]).split())


def parsed_page(path):
    parser = PageParser()
    parser.feed(path.read_text())
    return parser


def survey_page():
    parser = SurveyParser()
    parser.feed((ROOT / "dist/client/parent-questions.html").read_text())
    return parser


class PublicSiteContractTests(unittest.TestCase):
    def assertContains(self, needle, haystack):
        self.assertTrue(needle in haystack, f"missing required copy: {needle}")

    def assertNotContains(self, needle, haystack):
        self.assertFalse(needle in haystack, f"unexpected stale copy: {needle}")

    def test_homepage_separately_presents_verified_english_and_bengali_proposals(self):
        page = parsed_page(ROOT / "dist/client/index.html")
        english = " ".join(page.en)
        bengali = " ".join(page.bn)
        for expected in (
            "separate Qur’an and Arabic classes",
            "Qur’an 9:00–10:30 am",
            "Arabic 10:30 am–12:00 pm",
            "3:00–5:00 pm",
            "5:10–7:10 pm",
            "up to 10 learners",
            "৳4,000",
            "৳6,000",
            "৳3,500",
            "৳1,750",
            "not final or approved",
            "not accepting enrollment",
            "teacher names and qualifications",
            "child supervision",
            "authorized pickup",
            "emergency response",
            "parent complaint route",
        ):
            with self.subTest(language="English", expected=expected):
                self.assertContains(expected.lower(), english.lower())
        for expected in (
            "সকাল ৯টা",
            "দুপুর ১২টা",
            "বিকেল ৩টা–৫টা",
            "সন্ধ্যা ৭টা ১০",
            "সর্বোচ্চ ১০ জন",
            "৪,০০০ টাকা",
            "৬,০০০ টাকা",
            "৩,৫০০ টাকা",
            "১,৭৫০ টাকা",
            "এখনো ভর্তি শুরু হয়নি",
            "শিক্ষকদের নাম ও যোগ্যতা",
            "শিশুদের তত্ত্বাবধান",
            "জরুরি ব্যবস্থা",
        ):
            with self.subTest(language="Bengali", expected=expected):
                self.assertContains(expected, bengali)

    def test_research_questionnaire_has_consistent_schedule_and_separate_subjects(self):
        survey = survey_page()
        page_text = (ROOT / "dist/client/parent-questions.html").read_text()
        self.assertContains("সকাল ৯টা–১০টা ৩০", page_text)
        self.assertContains("সকাল ১০টা ৩০–দুপুর ১২টা", page_text)
        self.assertContains("বিকেল ৩টা–৫টা", page_text)
        self.assertContains("বিকেল ৫টা ১০–সন্ধ্যা ৭টা ১০", page_text)
        self.assertContains("আলাদা ক্লাসে একই সঙ্গে", page_text)
        self.assertContains("প্রতিটি বিষয়ের ব্যাচে সর্বোচ্চ ১০ জন", page_text)
        self.assertNotContains("৮০ মিনিট", page_text)
        self.assertNotContains("সর্বোচ্চ ২০ জন", page_text)

    def test_age_choices_match_age_question_and_existing_answer_order_is_retained(self):
        survey = survey_page()
        self.assertEqual(len(survey.fieldsets), 21)
        self.assertIn("বয়স", survey.legend(survey.fieldsets[0]))
        self.assertEqual(
            survey.fieldsets[0]["choices"],
            ["৫–৭ বছর", "৮–১০ বছর", "১১–১২ বছর"],
        )
        expected_ids = ["answer-1", "answer-1b"] + [f"answer-{number}" for number in range(2, 21)]
        self.assertEqual([item["textarea"][0] for item in survey.fieldsets], expected_ids)

    def test_shift_fit_question_covers_all_three_shifts(self):
        survey = survey_page()
        question = next(item for item in survey.fieldsets if survey.legend(item).startswith("১৩।"))
        self.assertContains("সকাল, বিকেল ও সন্ধ্যা", survey.legend(question))
        self.assertEqual(question["choices"], ["সকাল", "বিকেল", "সন্ধ্যা"])

    def test_schedule_preference_is_not_limited_to_after_school(self):
        survey = survey_page()
        question = next(item for item in survey.fieldsets if survey.legend(item).startswith("১০।"))
        self.assertNotContains("স্কুলের পর", survey.legend(question))
        self.assertEqual(
            question["choices"],
            ["সকালে ক্লাসে যাওয়া সম্ভব।", "বিকেলে ক্লাসে যাওয়া সম্ভব।", "সন্ধ্যায় ক্লাসে যাওয়া সম্ভব।"],
        )

    def test_bengali_research_discloses_proposed_fees_and_safeguarding_status(self):
        page = (ROOT / "dist/client/parent-questions.html").read_text()
        for expected in (
            "৪,০০০ টাকা",
            "৬,০০০ টাকা",
            "৩,৫০০ টাকা",
            "১,৭৫০ টাকা",
            "চূড়ান্ত বা অনুমোদিত নয়",
            "ভর্তি এখনো শুরু হয়নি",
            "তত্ত্বাবধান",
            "জরুরি ব্যবস্থা",
            "অভিযোগ জানানোর পথ",
            "ভর্তি আবেদন নয়",
            "গবেষণার জন্য",
        ):
            with self.subTest(expected=expected):
                self.assertContains(expected, page)

    def test_interviewer_guide_uses_the_same_schedule_capacity_and_proposed_fees(self):
        guide = (ROOT / "dist/client/parent-interview.html").read_text()
        for expected in (
            "Qur’an is proposed for 9:00–10:30 am, then Arabic for 10:30 am–noon",
            "separate, concurrent subject classes",
            "Each subject batch is capped at 10",
            "৳4,000 monthly for one subject or ৳6,000 for both",
            "৳3,500 per child",
            "Which subject and shift could your child realistically attend?",
        ):
            with self.subTest(expected=expected):
                self.assertContains(expected, guide)
        self.assertNotContains("80 minutes Hifz", guide)
        self.assertNotContains("Maximum 20 students per batch", guide)

    def test_worker_accepts_final_and_complete_form_responses(self):
        survey = survey_page()
        self.assertEqual(len(survey.fieldsets), 21)
        script = r'''
import Worker from "./dist/server/index.js";
const env = { DB: { prepare: () => ({ bind: () => ({ run: async () => ({ success: true }) }) }) } };
const post = async answers => {
  const response = await Worker.fetch(new Request("https://iqra.test/api/parent-responses", {
    method: "POST",
    headers: { Origin: "https://iqra.test", "Content-Type": "application/json" },
    body: JSON.stringify({ id: crypto.randomUUID(), answers })
  }), env);
  return response.status;
};
const item = n => ({ [n]: { note: `answer ${n}`, choices: [] } });
const all = Object.fromEntries(Array.from({ length: 21 }, (_, i) => [String(i + 1), { note: `answer ${i + 1}`, choices: [] }]));
console.log(JSON.stringify({ final: await post(item(21)), complete: await post(all) }));
'''
        result = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(json.loads(result.stdout), {"final": 200, "complete": 200})


if __name__ == "__main__":
    unittest.main()
