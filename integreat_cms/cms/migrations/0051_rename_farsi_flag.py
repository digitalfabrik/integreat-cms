# Generated by Django 3.2.16 on 2022-11-17 20:53
from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import migrations, models

if TYPE_CHECKING:
    from django.apps.registry import Apps
    from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def update_flag(
    apps: Apps,
    _schema_editor: BaseDatabaseSchemaEditor,
) -> None:
    """
    Migrate the flag name for Farsi

    :param apps: The configuration of installed applications
    """
    Language = apps.get_model("cms", "Language")
    Language.objects.filter(primary_country_code="fa").update(primary_country_code="fs")
    Language.objects.filter(secondary_country_code="fa").update(
        secondary_country_code="fs",
    )


class Migration(migrations.Migration):
    """
    Migrate the flag name for Farsi
    (see https://github.com/timoludwig/flagpack-dart-sass/pull/6)
    """

    dependencies = [
        ("cms", "0050_increase_max_url_length"),
    ]

    operations = [
        migrations.RunPython(update_flag, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="language",
            name="primary_country_code",
            field=models.CharField(
                choices=[
                    ("ab", "Arabic (non-political)"),
                    ("ad", "Andorra"),
                    ("ae", "United Arab Emirates"),
                    ("af", "Afghanistan"),
                    ("al", "Albania"),
                    ("am", "Armenia"),
                    ("ao", "Angola"),
                    ("ar", "Argentina"),
                    ("at", "Austria"),
                    ("au", "Australia"),
                    ("az", "Azerbaijan"),
                    ("ba", "Bosnia and Herzegovina"),
                    ("bd", "Bangladesh"),
                    ("be", "Belgium"),
                    ("bf", "Burkina Faso"),
                    ("bg", "Bulgaria"),
                    ("bh", "Bahrain"),
                    ("bi", "Burundi"),
                    ("bj", "Benin"),
                    ("bm", "Bermuda"),
                    ("bn", "Brunei"),
                    ("bo", "Bolivia"),
                    ("br", "Brazil"),
                    ("bt", "Bhutan"),
                    ("bw", "Botswana"),
                    ("by", "Belarus"),
                    ("ca", "Canada"),
                    ("cd", "Congo (Democratic Republic)"),
                    ("cf", "Central African Republic"),
                    ("cg", "Congo (Republic)"),
                    ("ch", "Switzerland"),
                    ("ci", "Côte d'Ivoire"),
                    ("cl", "Chile"),
                    ("cm", "Cameroon"),
                    ("cn", "China"),
                    ("co", "Colombia"),
                    ("cr", "Costa Rica"),
                    ("cu", "Cuba"),
                    ("cy", "Cyprus"),
                    ("cz", "Czechia"),
                    ("de", "Germany"),
                    ("dj", "Djibouti"),
                    ("dk", "Denmark"),
                    ("dm", "Dominica"),
                    ("do", "Dominican Republic"),
                    ("dz", "Algeria"),
                    ("ec", "Ecuador"),
                    ("ee", "Estonia"),
                    ("eg", "Egypt"),
                    ("er", "Eritrea"),
                    ("es", "Spain"),
                    ("et", "Ethiopia"),
                    ("fs", "Farsi (non-political)"),
                    ("fi", "Finland"),
                    ("fr", "France"),
                    ("ga", "Gabon"),
                    ("gb", "United Kingdom of Great Britain and Northern Ireland"),
                    ("gd", "Grenada"),
                    ("ge", "Georgia"),
                    ("gf", "French Guiana"),
                    ("gg", "Guernsey"),
                    ("gh", "Ghana"),
                    ("gi", "Gibraltar"),
                    ("gl", "Greenland"),
                    ("gm", "Gambia"),
                    ("gn", "Guinea"),
                    ("gp", "Guadeloupe"),
                    ("gr", "Greece"),
                    ("gt", "Guatemala"),
                    ("gu", "Guam"),
                    ("gy", "Guyana"),
                    ("hk", "Hong Kong"),
                    ("hn", "Honduras"),
                    ("hr", "Croatia"),
                    ("ht", "Haiti"),
                    ("hu", "Hungary"),
                    ("id", "Indonesia"),
                    ("ie", "Ireland"),
                    ("il", "Israel"),
                    ("in", "India"),
                    ("iq", "Iraq"),
                    ("ir", "Iran"),
                    ("is", "Iceland"),
                    ("it", "Italy"),
                    ("jm", "Jamaica"),
                    ("jo", "Jordan"),
                    ("jp", "Japan"),
                    ("ke", "Kenya"),
                    ("kg", "Kyrgyzstan"),
                    ("kh", "Cambodia"),
                    ("kp", "North Korea"),
                    ("kr", "South Korea"),
                    ("kw", "Kuwait"),
                    ("kz", "Kazakhstan"),
                    ("lb", "Lebanon"),
                    ("li", "Liechtenstein"),
                    ("lr", "Liberia"),
                    ("ls", "Lesotho"),
                    ("lt", "Lithuania"),
                    ("lu", "Luxembourg"),
                    ("lv", "Latvia"),
                    ("ly", "Libya"),
                    ("ma", "Morocco"),
                    ("mc", "Monaco"),
                    ("md", "Moldova"),
                    ("me", "Montenegro"),
                    ("mg", "Madagascar"),
                    ("mk", "North Macedonia"),
                    ("ml", "Mali"),
                    ("mm", "Myanmar"),
                    ("mn", "Mongolia"),
                    ("mr", "Mauritania"),
                    ("mt", "Malta"),
                    ("mu", "Mauritius"),
                    ("mv", "Maldives"),
                    ("mw", "Malawi"),
                    ("mx", "Mexico"),
                    ("my", "Malaysia"),
                    ("mz", "Mozambique"),
                    ("na", "Namibia"),
                    ("ne", "Niger"),
                    ("ng", "Nigeria"),
                    ("ni", "Nicaragua"),
                    ("nl", "Netherlands"),
                    ("no", "Norway"),
                    ("np", "Nepal"),
                    ("nz", "New Zealand"),
                    ("om", "Oman"),
                    ("pa", "Panama"),
                    ("pe", "Peru"),
                    ("pf", "French Polynesia"),
                    ("pg", "Papua New Guinea"),
                    ("ph", "Philippines"),
                    ("pk", "Pakistan"),
                    ("pl", "Poland"),
                    ("ps", "Palestine"),
                    ("pt", "Portugal"),
                    ("py", "Paraguay"),
                    ("qa", "Qatar"),
                    ("ro", "Romania"),
                    ("rs", "Serbia"),
                    ("ru", "Russian Federation"),
                    ("rw", "Rwanda"),
                    ("sa", "Saudi Arabia"),
                    ("sd", "Sudan"),
                    ("se", "Sweden"),
                    ("si", "Slovenia"),
                    ("sk", "Slovakia"),
                    ("sl", "Sierra Leone"),
                    ("sn", "Senegal"),
                    ("so", "Somalia"),
                    ("ss", "South Sudan"),
                    ("sv", "El Salvador"),
                    ("sy", "Syrian Arab Republic"),
                    ("td", "Chad"),
                    ("th", "Thailand"),
                    ("tj", "Tajikistan"),
                    ("tm", "Turkmenistan"),
                    ("tn", "Tunisia"),
                    ("tr", "Turkey"),
                    ("tw", "Taiwan"),
                    ("tz", "Tanzania"),
                    ("ua", "Ukraine"),
                    ("ug", "Uganda"),
                    ("us", "United States of America"),
                    ("uy", "Uruguay"),
                    ("uz", "Uzbekistan"),
                    ("ve", "Venezuela"),
                    ("vn", "Viet Nam"),
                    ("xk", "Kosovo"),
                    ("ye", "Yemen"),
                    ("za", "South Africa"),
                    ("zm", "Zambia"),
                    ("zw", "Zimbabwe"),
                ],
                help_text="The country with which this language is mainly associated. This flag is used to represent the language graphically.",
                max_length=2,
                verbose_name="primary country flag",
            ),
        ),
        migrations.AlterField(
            model_name="language",
            name="secondary_country_code",
            field=models.CharField(
                blank=True,
                choices=[
                    ("ab", "Arabic (non-political)"),
                    ("ad", "Andorra"),
                    ("ae", "United Arab Emirates"),
                    ("af", "Afghanistan"),
                    ("al", "Albania"),
                    ("am", "Armenia"),
                    ("ao", "Angola"),
                    ("ar", "Argentina"),
                    ("at", "Austria"),
                    ("au", "Australia"),
                    ("az", "Azerbaijan"),
                    ("ba", "Bosnia and Herzegovina"),
                    ("bd", "Bangladesh"),
                    ("be", "Belgium"),
                    ("bf", "Burkina Faso"),
                    ("bg", "Bulgaria"),
                    ("bh", "Bahrain"),
                    ("bi", "Burundi"),
                    ("bj", "Benin"),
                    ("bm", "Bermuda"),
                    ("bn", "Brunei"),
                    ("bo", "Bolivia"),
                    ("br", "Brazil"),
                    ("bt", "Bhutan"),
                    ("bw", "Botswana"),
                    ("by", "Belarus"),
                    ("ca", "Canada"),
                    ("cd", "Congo (Democratic Republic)"),
                    ("cf", "Central African Republic"),
                    ("cg", "Congo (Republic)"),
                    ("ch", "Switzerland"),
                    ("ci", "Côte d'Ivoire"),
                    ("cl", "Chile"),
                    ("cm", "Cameroon"),
                    ("cn", "China"),
                    ("co", "Colombia"),
                    ("cr", "Costa Rica"),
                    ("cu", "Cuba"),
                    ("cy", "Cyprus"),
                    ("cz", "Czechia"),
                    ("de", "Germany"),
                    ("dj", "Djibouti"),
                    ("dk", "Denmark"),
                    ("dm", "Dominica"),
                    ("do", "Dominican Republic"),
                    ("dz", "Algeria"),
                    ("ec", "Ecuador"),
                    ("ee", "Estonia"),
                    ("eg", "Egypt"),
                    ("er", "Eritrea"),
                    ("es", "Spain"),
                    ("et", "Ethiopia"),
                    ("fs", "Farsi (non-political)"),
                    ("fi", "Finland"),
                    ("fr", "France"),
                    ("ga", "Gabon"),
                    ("gb", "United Kingdom of Great Britain and Northern Ireland"),
                    ("gd", "Grenada"),
                    ("ge", "Georgia"),
                    ("gf", "French Guiana"),
                    ("gg", "Guernsey"),
                    ("gh", "Ghana"),
                    ("gi", "Gibraltar"),
                    ("gl", "Greenland"),
                    ("gm", "Gambia"),
                    ("gn", "Guinea"),
                    ("gp", "Guadeloupe"),
                    ("gr", "Greece"),
                    ("gt", "Guatemala"),
                    ("gu", "Guam"),
                    ("gy", "Guyana"),
                    ("hk", "Hong Kong"),
                    ("hn", "Honduras"),
                    ("hr", "Croatia"),
                    ("ht", "Haiti"),
                    ("hu", "Hungary"),
                    ("id", "Indonesia"),
                    ("ie", "Ireland"),
                    ("il", "Israel"),
                    ("in", "India"),
                    ("iq", "Iraq"),
                    ("ir", "Iran"),
                    ("is", "Iceland"),
                    ("it", "Italy"),
                    ("jm", "Jamaica"),
                    ("jo", "Jordan"),
                    ("jp", "Japan"),
                    ("ke", "Kenya"),
                    ("kg", "Kyrgyzstan"),
                    ("kh", "Cambodia"),
                    ("kp", "North Korea"),
                    ("kr", "South Korea"),
                    ("kw", "Kuwait"),
                    ("kz", "Kazakhstan"),
                    ("lb", "Lebanon"),
                    ("li", "Liechtenstein"),
                    ("lr", "Liberia"),
                    ("ls", "Lesotho"),
                    ("lt", "Lithuania"),
                    ("lu", "Luxembourg"),
                    ("lv", "Latvia"),
                    ("ly", "Libya"),
                    ("ma", "Morocco"),
                    ("mc", "Monaco"),
                    ("md", "Moldova"),
                    ("me", "Montenegro"),
                    ("mg", "Madagascar"),
                    ("mk", "North Macedonia"),
                    ("ml", "Mali"),
                    ("mm", "Myanmar"),
                    ("mn", "Mongolia"),
                    ("mr", "Mauritania"),
                    ("mt", "Malta"),
                    ("mu", "Mauritius"),
                    ("mv", "Maldives"),
                    ("mw", "Malawi"),
                    ("mx", "Mexico"),
                    ("my", "Malaysia"),
                    ("mz", "Mozambique"),
                    ("na", "Namibia"),
                    ("ne", "Niger"),
                    ("ng", "Nigeria"),
                    ("ni", "Nicaragua"),
                    ("nl", "Netherlands"),
                    ("no", "Norway"),
                    ("np", "Nepal"),
                    ("nz", "New Zealand"),
                    ("om", "Oman"),
                    ("pa", "Panama"),
                    ("pe", "Peru"),
                    ("pf", "French Polynesia"),
                    ("pg", "Papua New Guinea"),
                    ("ph", "Philippines"),
                    ("pk", "Pakistan"),
                    ("pl", "Poland"),
                    ("ps", "Palestine"),
                    ("pt", "Portugal"),
                    ("py", "Paraguay"),
                    ("qa", "Qatar"),
                    ("ro", "Romania"),
                    ("rs", "Serbia"),
                    ("ru", "Russian Federation"),
                    ("rw", "Rwanda"),
                    ("sa", "Saudi Arabia"),
                    ("sd", "Sudan"),
                    ("se", "Sweden"),
                    ("si", "Slovenia"),
                    ("sk", "Slovakia"),
                    ("sl", "Sierra Leone"),
                    ("sn", "Senegal"),
                    ("so", "Somalia"),
                    ("ss", "South Sudan"),
                    ("sv", "El Salvador"),
                    ("sy", "Syrian Arab Republic"),
                    ("td", "Chad"),
                    ("th", "Thailand"),
                    ("tj", "Tajikistan"),
                    ("tm", "Turkmenistan"),
                    ("tn", "Tunisia"),
                    ("tr", "Turkey"),
                    ("tw", "Taiwan"),
                    ("tz", "Tanzania"),
                    ("ua", "Ukraine"),
                    ("ug", "Uganda"),
                    ("us", "United States of America"),
                    ("uy", "Uruguay"),
                    ("uz", "Uzbekistan"),
                    ("ve", "Venezuela"),
                    ("vn", "Viet Nam"),
                    ("xk", "Kosovo"),
                    ("ye", "Yemen"),
                    ("za", "South Africa"),
                    ("zm", "Zambia"),
                    ("zw", "Zimbabwe"),
                ],
                help_text="Another country with which this language is also associated. This flag is used in the language switcher.",
                max_length=2,
                verbose_name="secondary country flag",
            ),
        ),
    ]
