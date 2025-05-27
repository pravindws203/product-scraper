import pandas as pd


def add_image_url_count_column(csv_path: str) -> None:
  try:
    df = pd.read_csv(csv_path)
    
    # Count valid image URLs per row
    url_columns = [f'image_url_{i}' for i in range(1, 11)]
    df['image_url_count'] = df[url_columns].apply(
      lambda row: row.notna().sum(), axis=1
    )
    
    # Insert the column before image_url_1
    if 'image_url_1' in df.columns:
      insert_pos = df.columns.get_loc('image_url_1')
      count_column = df.pop('image_url_count')
      df.insert(loc=insert_pos, column='image_url_count', value=count_column)
    else:
      print("[!] 'image_url_1' column not found. 'image_url_count' added at end.")
    
    # Save to the same CSV
    df.to_csv(csv_path, index=False)
    print(f"[✔] image_url_count column added and saved to: {csv_path}")
  
  except Exception as e:
    print(f"[✖] Error processing CSV: {e}")