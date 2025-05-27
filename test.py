from Amazon import Amazon
from Jiomart import Jiomart
from HerbalBAPS import HerbalBAPS


def main():
  # Initialize the search with optional headless mode
  amazon_screpped = Amazon(headless=False)  # Set headless=True for no browser window
  herbal_baps_screpped = HerbalBAPS(headless=False)
  scrapped = Jiomart(headless=False)  # Set headless=True for no browser window
  # Perform the search
  # herbal_baps_screpped.scrape_category("https://herbal.baps.org/spices-and-condiments.html")
  amazon_screpped.scrape_category("https://www.amazon.in/stores/STROOM/page/76F88A2A-830A-4E74-8F69-15BF62F1AC20?lp_asin=B0DJWL3WHP&ref_=cm_sw_r_apin_ast_store_N7A8T6YA6D9GVEVBW78Z&store_ref=bl_ast_dp_brandLogo_sto")
  # scrapped.scrape_category("https://www.jiomart.com/groceries/b/haldiram-s-nagpur/193803")
  # print(details)
  # for k, v in details.items():
  #   print(f"{k}: {v}")
  # Process results
  # if result_url:
  #   print(f"\nSuccess! Found URL: {result_url}")
  # else:
  #   print("\nTarget URL not found after multiple attempts")


if __name__ == "__main__":
  main()