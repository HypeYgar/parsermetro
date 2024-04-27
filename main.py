import asyncio
import aiohttp
from bs4 import BeautifulSoup
import urllib.parse
import json

base_url = "https://online.metro-cc.ru/category/avtotovary/avtokosmetika-aksessuary"

async def scrape_page(session, page_number):
    async with session.get(f"{base_url}?page={page_number}") as response:
        if response.status == 200:
            soup = BeautifulSoup(await response.text(), 'html.parser')
            product_cards = soup.find_all("div", class_="catalog-2-level-product-card")
            print(f"Страница {page_number}:")
            products = []
            for card in product_cards:
                product_title_element = card.find("span", class_="product-card-name__text")
                product_title = product_title_element.text.strip() if product_title_element else None

                product_title_element = card.find("p", class_="product-title")
                is_out_of_stock = product_title_element.get("is-out-of-stock") if product_title_element else None

                if is_out_of_stock == "true":
                    print("Товар раскуплен")
                    continue

                product_id = card.get("id")
                product_link_element = card.find("a", class_="product-card-photo__link")
                product_href = urllib.parse.urljoin(base_url, product_link_element.get("href")) if product_link_element else None
                product_price_actual_element = card.find("span", class_="product-unit-prices__actual")
                product_price_old_element = card.find("span", class_="product-unit-prices__old")
                product_price_actual = product_price_actual_element.find("span", class_="product-price__sum-rubles").text if product_price_actual_element else None
                product_price_old = product_price_old_element.find("span", class_="product-price__sum-rubles").text if product_price_old_element else None
                if product_id and product_href and product_title and product_price_actual:
                    product_data = {
                        "id": product_id,
                        "title": product_title,
                        "href": product_href,
                        "price_actual": product_price_actual,
                        "price_old": product_price_old,
                    }
                    async with session.get(product_href) as product_response:
                        if product_response.status == 200:
                            product_soup = BeautifulSoup(await product_response.text(), 'html.parser')
                            nigrin_element = product_soup.find("a", class_="product-attributes__list-item-link")
                            nigrin = nigrin_element.text.strip() if nigrin_element else None
                            if nigrin:
                                product_data["brand"] = nigrin
                        else:
                            print(f"Ошибка при получении страницы {product_href}: {product_response.status}")
                    products.append(product_data)
                else:
                    print("Не удалось извлечь информацию о товаре.")
            print("-----------------------------------------")
            return products
        else:
            print(f"Ошибка при получении страницы {base_url}?page={page_number}: {response.status}")
            return []

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [scrape_page(session, page_number) for page_number in range(1, 10)]
        results = await asyncio.gather(*tasks)

    all_products = []
    for result in results:
        all_products.extend(result)

    with open("scraped_data.json", "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    asyncio.run(main())
