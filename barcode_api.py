import requests
import json
from tqdm import tqdm

def get_ids():
  """Retrieve all IDs with 'raw' status from the database."""
  try:
    url = "http://10.0.101.153:10000/barcodeids"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        id_list = data.get("id", [])
        return id_list
    else:
        print("Error fetching IDs:", response.status_code)
        return []
  except Exception as e:
      print("Error:", e)
      return []

def get_images(id):
    """Retrieve images for a given ID from the database."""
    try:
      url = "http://10.0.101.153:10000/images"
      payload = {"id": id}
      response = requests.post(url, json=payload)
      if response.status_code == 200:
          data = response.json()
          return data
      else:
          print("Error fetching images:", response.status_code)
          return None
    except Exception as e:
        print("Error:", e)
        return None

def update_barcode(id, barcode):
    """Update barcode for a given ID in the database."""
    try:
        url = "http://10.0.101.153:10000/barcode"
        payload = {"id": id, "barcode": barcode}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print("Error updating barcode:", response.status_code)
            return None
    except Exception as e:
        print("Error:", e)
        return None
    
def get_barcode(image_url):
    """Retrieve barcode for a given image URL from the database."""
    try:
        url = "http://10.0.101.153:8000/scan/url"
        payload = {"image_url": image_url}
        headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "X-API-Key": 'your-secret-api-key'
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"Error fetching barcode, status code: {response.status_code}")
            print(f"Response content: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def main():
    """Main function to fetch IDs and print them."""
    ids = get_ids()
    
    pbar = tqdm(total=len(ids), initial=0, desc="Amazon Scrapped Products", unit="products", dynamic_ncols=True)
    for id in ids:
      images = get_images(id)
      for image in images.get('main_images', []) + images.get('other_images', []):
        if not image:
          continue
          
        barcode_data = get_barcode(image)
        if barcode_data.get('status') == 'success':
          barcode = barcode_data.get('barcode_data')
          if barcode:
            data = update_barcode(id, barcode)
            pbar.set_postfix({"Inserted product with ID": data.get('id')})
            break
          else:
            print(f"ID: {id}, No barcode found")
        
      pbar.update(1)
      
if __name__ == "__main__":
    main()