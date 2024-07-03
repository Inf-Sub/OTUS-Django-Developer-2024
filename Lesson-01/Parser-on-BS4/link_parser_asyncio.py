from bs4 import BeautifulSoup
from urllib.parse import urlparse
import os
import sys
import time
import datetime
import aiohttp
import asyncio


def format_link_output(link: str, count: int, global_count: int, level: int):
    """
    Форматирует строку вывода для ссылки.
    """
    return f'count: {count:03} / {global_count:08}\t| depth: {level}\t| link: {link}'


def create_filename_with_timestamp(original_filename: str):
    # Получаем текущую дату и время
    now = datetime.datetime.now()
    # Форматируем строку времени (ггггммдд_ччммсс)
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    # Разбиваем исходное имя файла на имя и расширение
    name, extension = original_filename.rsplit('.', 1)
    # Создаем новое имя файла, добавляя к нему отметку времени
    new_filename = f"{name}_{timestamp}.{extension}"
    return new_filename


async def fetch_external_links(session, url):
    """
    Асинхронная функция для извлечения всех внешних ссылок на заданной веб-странице. Игнорирует внутренние ссылки.
    """
    try:
        async with session.get(url) as response:
            text = await response.text()
            soup = BeautifulSoup(text, 'html.parser')
            links = set()

            parsed_url = urlparse(url)
            base_domain = f'{parsed_url.scheme}://{parsed_url.netloc}'

            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('http'):
                    parsed_href = urlparse(href)
                    href_domain = f'{parsed_href.scheme}://{parsed_href.netloc}'
                    if href_domain != base_domain:
                        links.add(href)

            return links
    except Exception as e:
        print(f'Ошибка при запросе к {url}: {str(e)}')
        return set()


async def recursive_link_fetch(
        session, url: str, depth: int = 1, output: str = 'both', file_path: str = 'result/result.txt', level: int = 1
) -> None:
    links = await fetch_external_links(session, url)
    links_counter = make_counter()

    output_lines = [f'Ссылки, найденные на {url}:']
    for link in links:
        formatted_line = format_link_output(link, links_counter(), global_links_counter(), level)
        output_lines.append(formatted_line)

    if output in ('terminal', 'both'):
        for line in output_lines:
            print(line)
    if output in ('file', 'both'):
        with open(file_path, 'a', encoding='utf-8') as file:
            for line in output_lines:
                file.write(line + '\n')

    if depth > 1:
        tasks = [recursive_link_fetch(
            session=session, url=link, depth=depth - 1, output=output, file_path=file_path, level=level + 1
        ) for link in links]

        await asyncio.gather(*tasks)


def make_counter():
    count = 0

    def counter():
        nonlocal count
        count += 1
        return count
    return counter


async def main(argv: list):
    if len(argv) > 1:
        url = argv[1]
        depth = int(argv[2]) if len(argv) > 2 and argv[2] else 1
        output = argv[3] if len(argv) > 3 and argv[3] else 'terminal'

        folder_path = 'result'
        file_name = 'links_asyncio.txt'

        new_filename = create_filename_with_timestamp(file_name)

        # Проверка существования папки и создание если она отсутствует
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # Путь к файлу внутри папки
        file_path = os.path.join(folder_path, new_filename)

        async with aiohttp.ClientSession() as session:
            await recursive_link_fetch(session, url=url, depth=depth, output=output, file_path=file_path)
    else:
        print("Usage: python script.py <url> <depth> <output>")


if __name__ == "__main__":
    start_time = time.time()
    # Создание счетчика
    global_links_counter = make_counter()

    asyncio.run(main(sys.argv))
    print("--- {:.2f} seconds ---".format(time.time() - start_time))
