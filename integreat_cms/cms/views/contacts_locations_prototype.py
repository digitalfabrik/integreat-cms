"""
PROTOTYPE: views of the combined "Orte & Kontakte" page for the user test.

All data is fake and lives in the session of the logged in user (no database).
New places/contacts, categories and removed links are kept until the session ends
or the tester data is reset via /<region>/contacts-locations/reset/.
"""

from __future__ import annotations

import copy

from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

SESSION_KEY = "proto_contacts_locations"

PLACE_CATEGORIES = [
    "Behörde/Amt",
    "Beratung",
    "Bildung",
    "Dienstleistung",
    "Einkaufen",
    "Einrichtung",
    "Freizeit",
    "Gastronomie",
    "Gesundheit",
    "Kultur",
    "Mobilität",
    "Multimedia",
    "Sonstiges",
    "Treffpunkt",
]

# Target languages of the translation view, "translations" of a place has one status per language: c = aktuell, m = maschinell, x = fehlt
LANGUAGES = ["AR", "BG", "CS", "DA", "EL", "EN", "ES", "FA", "FI", "FR", "HI", "HR", "HU", "ID", "IT", "KA", "KO", "KMR", "LT", "NL", "PL", "PT", "RO"]

# Fake places in Augsburg: invented names and house numbers, no real institution data
FAKE_PLACES = [
    {"id": 1, "title": "Ausländerbehörde", "categories": ["Behörde/Amt"], "street": "Langenmantelstraße 14", "zip": "86153", "town": "Augsburg", "published": True, "translations": "ccccccccmcccccccccccccc"},
    {"id": 2, "title": "Bürgerbüro Haunstetten", "categories": ["Behörde/Amt", "Dienstleistung"], "street": "Tattenbachstraße 7", "zip": "86179", "town": "Augsburg", "published": True, "translations": "cccccccccccccccccccccmm"},
    {"id": 3, "title": "Agentur für Arbeit", "categories": ["Behörde/Amt", "Beratung"], "street": "Halderstraße 22", "zip": "86150", "town": "Augsburg", "published": True, "translations": "ccccccmmmmmmmcccccccccc"},
    {"id": 4, "title": "Migrationsberatung Lechhausen", "categories": ["Beratung"], "street": "Neuburger Straße 41", "zip": "86167", "town": "Augsburg", "published": True, "translations": "ccccccccccccccccccccccc"},
    {"id": 5, "title": "Sprachcafé im Bürgerhaus Pfersee", "categories": ["Treffpunkt", "Bildung"], "street": "Stadtberger Straße 18", "zip": "86157", "town": "Augsburg", "published": True, "translations": "ccccccccccccmmmmccccccc"},
    {"id": 6, "title": "Volkshochschule – Kursräume Innenstadt", "categories": ["Bildung"], "street": "Willy-Brandt-Platz 3", "zip": "86153", "town": "Augsburg", "published": True, "translations": "ccccccccccccccccccccccc"},
    {"id": 7, "title": "Stadtteilbibliothek Oberhausen", "categories": ["Bildung", "Multimedia"], "street": "Donauwörther Straße 63", "zip": "86154", "town": "Augsburg", "published": False, "translations": "mmmmmmmmmmmmmmmmmmmmmmm"},
    {"id": 8, "title": "Kinderarztpraxis Dr. Yilmaz", "categories": ["Gesundheit"], "street": "Ulmer Straße 112", "zip": "86156", "town": "Augsburg", "published": True, "translations": "ccccccccccccccccccccccc"},
    {"id": 9, "title": "Gesundheitsamt", "categories": ["Behörde/Amt", "Gesundheit"], "street": "Karmelitengasse 9", "zip": "86152", "town": "Augsburg", "published": True, "translations": "ccccccccccccccccccccccc"},
    {"id": 10, "title": "Familientreff Herrenbach", "categories": ["Treffpunkt", "Freizeit"], "street": "Reichenberger Straße 30", "zip": "86161", "town": "Augsburg", "published": True, "translations": "cccccccmmmmcccccccccccc"},
    {"id": 11, "title": "Sozialkaufhaus Fundgrube", "categories": ["Einkaufen", "Einrichtung"], "street": "Holzbachstraße 25", "zip": "86152", "town": "Augsburg", "published": True, "translations": "ccccccccccccccccccccccc"},
    {"id": 12, "title": "Fahrradwerkstatt zum Selbermachen", "categories": ["Mobilität", "Dienstleistung"], "street": "Gögginger Straße 59", "zip": "86159", "town": "Augsburg", "published": False, "translations": "mmmmmmmmmmmmmmmmmmmmmmm"},
    {"id": 13, "title": "Internationaler Mittagstisch", "categories": ["Gastronomie", "Treffpunkt"], "street": "Jakoberstraße 40", "zip": "86152", "town": "Augsburg", "published": True, "translations": "ccccccccccccccccccccccc"},
    {"id": 14, "title": "Kulturhaus am Kanal", "categories": ["Kultur", "Freizeit"], "street": "Mittlerer Lech 8", "zip": "86150", "town": "Augsburg", "published": True, "translations": "cccccccccccccccccccccmm"},
]

# Fake contacts: "places" are place ids, "pages" are only titles
FAKE_CONTACTS = [
    {"id": 1, "name": "Aylin Demir", "role": "Sachbearbeiterin Aufenthaltstitel", "email": "a.demir@augsburg.example", "places": [1], "pages": ["Aufenthalt und Visum"]},
    {"id": 2, "name": "Thomas Berger", "role": "Teamleitung Bürgerbüro", "email": "t.berger@augsburg.example", "places": [2], "pages": []},
    {"id": 3, "name": "Marina Kovač", "role": "Arbeitsvermittlerin", "email": "m.kovac@augsburg.example", "places": [3], "pages": ["Arbeit finden"]},
    {"id": 4, "name": "Samir Haddad", "role": "Migrationsberater", "email": "s.haddad@augsburg.example", "places": [4], "pages": ["Beratung für Geflüchtete", "Familiennachzug"]},
    {"id": 5, "name": "Julia Hofmann", "role": "Ehrenamtskoordination", "email": "j.hofmann@augsburg.example", "places": [5, 10], "pages": ["Ehrenamt in Augsburg"]},
    {"id": 6, "name": "Petra Lang", "role": "Kursberatung Deutschkurse", "email": "p.lang@augsburg.example", "places": [6], "pages": ["Deutsch lernen"]},
    {"id": 7, "name": "Lukas Wagner", "role": "Bibliothekar", "email": "l.wagner@augsburg.example", "places": [7], "pages": []},
    {"id": 8, "name": "Dr. Emre Yilmaz", "role": "Kinderarzt", "email": "praxis.yilmaz@augsburg.example", "places": [8], "pages": ["Ärztinnen und Ärzte"]},
    {"id": 9, "name": "Sabine Richter", "role": "Impfberatung", "email": "s.richter@augsburg.example", "places": [9], "pages": ["Impfungen"]},
    {"id": 10, "name": "Olena Shevchenko", "role": "Sozialpädagogin", "email": "o.shevchenko@augsburg.example", "places": [10], "pages": ["Angebote für Familien"]},
    {"id": 11, "name": "Michael Huber", "role": "Filialleitung", "email": "m.huber@augsburg.example", "places": [11], "pages": []},
    {"id": 12, "name": "Ahmad Rahimi", "role": "Werkstattleitung", "email": "a.rahimi@augsburg.example", "places": [12], "pages": []},
    {"id": 13, "name": "Grace Mensah", "role": "Projektleitung", "email": "g.mensah@augsburg.example", "places": [13], "pages": ["Treffpunkte und Cafés"]},
    {"id": 14, "name": "Hannah Schuster", "role": "Programmleitung", "email": "h.schuster@augsburg.example", "places": [14], "pages": []},
    {"id": 15, "name": "Infotelefon Integration", "role": "Telefonberatung", "email": "info-integration@augsburg.example", "places": [], "pages": ["Wichtige Telefonnummern"]},
]

OPENING_HOURS = [
    ("Montag", "09:00 - 16:00", False),
    ("Dienstag", "09:00 - 16:00", False),
    ("Mittwoch", "09:00 - 12:00", False),
    ("Donnerstag", "09:00 - 18:00", False),
    ("Freitag", "09:00 - 12:00", False),
    ("Samstag", "geschlossen", False),
    ("Sonntag", "geschlossen", False),
]
EMPTY_OPENING_HOURS = [(day, "keine Angabe", True) for day, _, _ in OPENING_HOURS]

PLACE_EDIT_TABS = [
    ("texte", "Texte & Übersetzungen"),
    ("infos", "Orts-Infos & Einstellungen"),
    ("verknuepfungen", "Verknüpfungen"),
]
CONTACT_EDIT_TABS = [
    ("infos", "Kontakt-Informationen"),
    ("verknuepfungen", "Verknüpfungen"),
]


def _data(request):
    data = request.session.get(SESSION_KEY)
    if data is None:
        data = {
            "places": copy.deepcopy(FAKE_PLACES),
            "contacts": copy.deepcopy(FAKE_CONTACTS),
            "next_id": 100,
        }
        request.session[SESSION_KEY] = data
    return data


def _save(request, data):
    request.session[SESSION_KEY] = data
    request.session.modified = True


def _places(data):
    """Places sorted A-Z with their linked contacts and the combined city line"""
    result = []
    for place in sorted(data["places"], key=lambda p: p["title"].lower()):
        result.append(
            {
                **place,
                "city": f"{place['zip']} {place['town']}".strip(),
                "contacts": [c for c in data["contacts"] if place["id"] in c["places"]],
            }
        )
    return result


def _contacts(data):
    """Contacts sorted A-Z with place titles instead of ids"""
    titles = {p["id"]: p["title"] for p in data["places"]}
    result = []
    for contact in sorted(data["contacts"], key=lambda c: c["name"].lower()):
        result.append({**contact, "place_ids": contact["places"], "places": [titles[i] for i in contact["places"] if i in titles]})
    return result


def _find(items, item_id):
    for item in items:
        if item["id"] == item_id:
            return item
    raise Http404("Gibt es im Prototyp nicht")


def _new_id(data):
    data["next_id"] += 1
    return data["next_id"]


def _list_url(region_slug, tab):
    return reverse("contacts_locations", kwargs={"region_slug": region_slug}) + f"?tab={tab}"


def _place_url(region_slug, place_id, tab=None):
    url = reverse("contacts_locations_place_edit", kwargs={"region_slug": region_slug, "place_id": place_id})
    return f"{url}?tab={tab}" if tab else url


@never_cache
def overview(request, region_slug):
    data = _data(request)
    return render(
        request,
        "contacts_locations/contacts_locations.html",
        {
            "current_menu_item": "contacts_locations",
            "tabs": [("orte", "Orte"), ("kontakte", "Kontakte")],
            "fake_place_categories": PLACE_CATEGORIES,
            "fake_languages": LANGUAGES,
            "fake_places": _places(data),
            "fake_contacts": _contacts(data),
        },
    )


@require_POST
def new_place(request, region_slug):
    data = _data(request)
    place_id = _new_id(data)
    title = request.POST.get("title", "").strip() or "Neuer Ort"
    categories = [c for c in PLACE_CATEGORIES if c in request.POST.getlist("categories")]
    # PROTOTYPE: the test task place always gets these categories, whatever was picked in the overlay
    if "nachbarschaftszentrum" in title.lower():
        categories = ["Beratung", "Treffpunkt"]
    data["places"].append(
        {
            "id": place_id,
            "title": title,
            "categories": categories,
            "street": request.POST.get("street", "").strip(),
            "zip": request.POST.get("zip", "").strip(),
            "town": request.POST.get("town", "").strip(),
            "published": False,
            "translations": "x" * len(LANGUAGES),
            "new": True,
        }
    )
    _save(request, data)
    if request.POST.get("action") == "edit":
        return redirect(_place_url(region_slug, place_id))
    return redirect(_list_url(region_slug, "orte"))


@require_POST
def new_contact(request, region_slug):
    data = _data(request)
    contact_id = _new_id(data)
    place_ids = []
    if request.POST.get("new-contact-location") == "place" and request.POST.get("place_id", "").isdigit():
        place_ids = [int(request.POST["place_id"])]
    data["contacts"].append(
        {
            "id": contact_id,
            "name": request.POST.get("name", "").strip() or "Neuer Kontakt",
            "role": "",
            "email": "",
            "places": place_ids,
            "pages": [],
            "new": True,
        }
    )
    _save(request, data)
    if request.POST.get("action") == "edit":
        return redirect(reverse("contacts_locations_contact_edit", kwargs={"region_slug": region_slug, "contact_id": contact_id}))
    return redirect(_list_url(region_slug, "kontakte"))


@never_cache
def place_edit(request, region_slug, place_id):
    data = _data(request)
    place = _find(_places(data), place_id)
    states = {"c": "done", "m": "machine", "x": "missing"}
    return render(
        request,
        "contacts_locations/place_edit.html",
        {
            "current_menu_item": "contacts_locations",
            "edit_tabs": PLACE_EDIT_TABS,
            "fake_place_categories": PLACE_CATEGORIES,
            "place": place,
            "fake_opening_hours": EMPTY_OPENING_HOURS if place.get("new") else OPENING_HOURS,
            "fake_place_contacts": place["contacts"],
            # Contacts for the "Verknüpfung hinzufügen" overlay: all that are not linked to this place yet, A-Z
            "fake_link_contacts": [c for c in _contacts(data) if place_id not in c["place_ids"]],
            "fake_translations": [(code, states[s]) for code, s in zip(LANGUAGES, place["translations"])],
        },
    )


@require_POST
def place_categories(request, region_slug, place_id):
    data = _data(request)
    place = _find(data["places"], place_id)
    place["categories"] = [c for c in PLACE_CATEGORIES if c in request.POST.getlist("categories")]
    _save(request, data)
    return redirect(_place_url(region_slug, place_id, "infos"))


@require_POST
def place_unlink(request, region_slug, place_id):
    data = _data(request)
    contact = _find(data["contacts"], int(request.POST.get("contact_id", 0)))
    contact["places"] = [i for i in contact["places"] if i != place_id]
    _save(request, data)
    return redirect(_place_url(region_slug, place_id, "verknuepfungen"))


@require_POST
def place_link(request, region_slug, place_id):
    """PROTOTYPE: link the contact picked in the "Verknüpfung hinzufügen" overlay to this place"""
    data = _data(request)
    if request.POST.get("contact_id", "").isdigit():
        contact = _find(data["contacts"], int(request.POST["contact_id"]))
        if place_id not in contact["places"]:
            contact["places"].append(place_id)
        _save(request, data)
    return redirect(_place_url(region_slug, place_id, "verknuepfungen"))


@never_cache
def contact_edit(request, region_slug, contact_id):
    data = _data(request)
    contact = _find(_contacts(data), contact_id)
    return render(
        request,
        "contacts_locations/contact_edit.html",
        {
            "current_menu_item": "contacts_locations",
            "edit_tabs": CONTACT_EDIT_TABS,
            "fake_places": _places(data),
            "contact": contact,
        },
    )


@require_POST
def contact_save(request, region_slug, contact_id):
    """PROTOTYPE: store the inputs of the Kontakt-Informationen tab in the session data"""
    data = _data(request)
    contact = _find(data["contacts"], contact_id)
    contact["name"] = request.POST.get("name", "").strip() or contact["name"]
    for field in ("role", "email", "phone", "mobile", "website", "appointment_url"):
        contact[field] = request.POST.get(field, "").strip()
    _save(request, data)
    return redirect(_list_url(region_slug, "kontakte"))


def reset(request, region_slug):
    """Hidden URL for the test moderator: back to the initial fake data"""
    request.session.pop(SESSION_KEY, None)
    return redirect(_list_url(region_slug, "orte"))
