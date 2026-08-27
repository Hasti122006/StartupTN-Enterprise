from utils import extract_company_cards_from_listing_html


def test_extract_company_cards_from_listing_html():
    html = """
    <div class="MuiPaper-root MuiCard-root eco-card-resp css-s18byi">
      <div class="MuiCardContent-root css-1iktuhs">
        <p class="crd-title-text m-0">AMIZHTH TECHNO SOLUTIONS PRIVATE LIMITED</p>
        <span class="crd-span-text">DPIIT Startup</span>
      </div>
      <img alt="crd-img" src="https://example.com/logo.png" />
    </div>
    <div class="MuiPaper-root MuiCard-root eco-card-resp css-s18byi">
      <div class="MuiCardContent-root css-1iktuhs">
        <p class="crd-title-text m-0">Dharshan Brothers Technologies Private Limited</p>
        <span class="crd-span-text">DPIIT Startup</span>
      </div>
      <img alt="crd-img" src="https://example.com/logo2.png" />
    </div>
    """

    cards = extract_company_cards_from_listing_html(html)

    assert len(cards) == 2
    assert cards[0]["company_name"] == "AMIZHTH TECHNO SOLUTIONS PRIVATE LIMITED"
    assert cards[0]["startup_type"] == "DPIIT Startup"
    assert cards[0]["logo_url"] == "https://example.com/logo.png"
    assert cards[1]["company_name"] == "Dharshan Brothers Technologies Private Limited"
