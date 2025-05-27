from mysql_db import MySQLDB
import json
import requests

db = MySQLDB(
      host="localhost",
      user="root",
      password="Admin@123",
      database="Product_Webscrapping"
    )

columns = [
  "webside",
  "product_url",
  "variant_id",
  "name",
  "brand",
  "barcode",
  "ingredients",
  "allergen",
  "nutritional_info",
  "price",
  "dietary_preference",
  "unit_of_measure",
  "weight_in_gms",
  "packsize",
  "image_url_1",
  "image_url_2",
  "image_url_3",
  "image_url_4",
  "image_url_5",
  "image_url_6",
  "image_url_7",
  "image_url_8",
  "image_url_9",
  "image_url_10",
  
]


def extract_image_urls_text(image_urls) -> str:
  """
  Extracts image URLs from the tuple (starting from index 22),
  filters only valid URLs (starts with http),
  and returns them as a JSON string in the format:
  { "image_urls": [ ... ] }
  """
  # image_urls = [url for url in image_url[22:] if isinstance(url, str) and url.startswith("http")]
  if not image_urls:
    return ""
  return json.dumps({"image_urls": image_urls}, indent=2)

data = db.get_data("scraped_product", columns, "brand like '%stroom%'")
for row in data:
  images = []
  for i in range(1, 11):
    if row.get(f"image_url_{i}") == '':
      break
    images.append(row.get(f"image_url_{i}"))
  product = {
    "variant_id": row.get("variant_id"),
    "name": row.get("name"),
    "product_url": row.get("product_url"),
    "brand_name": row.get("brand"),
    "category": None,
    "sub_category": None,
    "allergen_information": row.get("allergen", None),
    "mass_measurement_unit": row.get("unit_of_measure", None),
    "net_weight": row.get("weight_in_gms", None),
    "mrp": row.get("price", None),
    "ingredients_main_ocr": row.get("ingredients", None),
    "nutrients_main_ocr": row.get("nutritional_info", None),
    "images": extract_image_urls_text(images),
    "front_img": None,
    "back_img": None,
    "nutrients_img": None,
    "ingredients_img": None,
    "source": "Zepto",
    "status": "raw",
  }
  url = "http://10.0.101.153:10000/insert"
  response = requests.post(url, json=product)
  if response.status_code == 200:
    print("insert")
  else:
    print("not insert")
  
  data = response.json()
  print(data)