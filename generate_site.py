# generate_site.py (ФИНАЛЬНАЯ ВЕРСИЯ 5.0 - С ПОИСКОМ)

import markdown
import os
import re
from bs4 import BeautifulSoup
from slugify import slugify
import webbrowser
import json # <<< НОВЫЙ ИМПОРТ

# --- НАСТРОЙКИ ---
INPUT_MD_DIR = 'docs'
CSS_FILE = 'style.css'
OUTPUT_HTML_FILE = 'notes.html'
PAGE_LOGO_TEXT = "Purple Notes"
SITE_TITLE = "Purple Notes"
SEARCH_INDEX_FILE = 'search-index.json' # <<< НОВАЯ НАСТРОЙКА

# --- ИКОНКИ ---
COPY_ICON_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>'
COPIED_ICON_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>'
CHEVRON_RIGHT_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="nav-chevron"><polyline points="9 18 15 12 9 6"></polyline></svg>'
SEARCH_ICON_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="search-icon"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>'
# ... после SEARCH_ICON_SVG
MENU_ICON_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>'
# <<< ЗАМЕНИТЕ ВАШ JAVASCRIPT_CODE НА ЭТОТ >>>
JAVASCRIPT_CODE = f"""
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/minisearch@6.3.0/dist/umd/index.min.js"></script>
<script>
document.addEventListener('DOMContentLoaded', async () => {{
    // ... (весь ваш код от подсветки до поиска остается здесь без изменений) ...

    // 1. ПОДСВЕТКА КОДА
    document.querySelectorAll('pre code:not(.nohighlight)').forEach((block) => {{
        hljs.highlightElement(block);
    }});

    // 2. ПЕРЕКЛЮЧАТЕЛЬ ТЕМЫ
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark-mode') {{
        body.classList.add('dark-mode');
        themeToggle.checked = true;
    }}
    themeToggle.addEventListener('change', () => {{
        body.classList.toggle('dark-mode', themeToggle.checked);
        localStorage.setItem('theme', themeToggle.checked ? 'dark-mode' : 'light-mode');
    }});

    // 3. КНОПКИ "КОПИРОВАТЬ"
    document.querySelectorAll('.copy-button').forEach(button => {{
        const originalContent = button.innerHTML;
        button.addEventListener('click', () => {{
            const pre = button.closest('pre');
            const code = pre.querySelector('code');
            navigator.clipboard.writeText(code.innerText).then(() => {{
                button.innerHTML = `{COPIED_ICON_SVG} Скопировано!`;
                button.classList.add('copied');
                setTimeout(() => {{
                    button.innerHTML = originalContent;
                    button.classList.remove('copied');
                }}, 2000);
            }});
        }});
    }});
    
    // 4. ЛОГИКА ОГЛАВЛЕНИЯ "НА ЭТОЙ СТРАНИЦЕ"
    let currentObserver = null;
    const setupIntersectionObserver = (sectionId) => {{
        if (currentObserver) {{ currentObserver.disconnect(); }}
        const section = document.getElementById(sectionId);
        const toc = document.getElementById(`toc-${{sectionId}}`);
        if (!section || !toc) return;
        const headings = Array.from(section.querySelectorAll('h2, h3'));
        const tocLinks = toc.querySelectorAll('a');
        if (headings.length === 0 || tocLinks.length === 0) return;
        currentObserver = new IntersectionObserver(entries => {{
            entries.forEach(entry => {{
                const id = entry.target.getAttribute('id');
                const tocLink = toc.querySelector(`a[href="#${{id}}"]`);
                if (entry.isIntersecting && tocLink) {{
                    tocLinks.forEach(link => link.parentElement.classList.remove('active'));
                    tocLink.parentElement.classList.add('active');
                }}
            }});
        }}, {{ rootMargin: "0px 0px -80% 0px" }});
        headings.forEach(heading => currentObserver.observe(heading));
    }};
    
    // 5. ЛОГИКА СВОРАЧИВАЕМЫХ МЕНЮ
    document.querySelectorAll('.nav-category-toggle').forEach(toggle => {{
        toggle.addEventListener('click', () => {{
            toggle.parentElement.classList.toggle('is-open');
        }});
    }});

    // 6. ФУНКЦИОНАЛ ПОИСКА С MINISEARCH
    const searchInput = document.getElementById('search-input');
    const searchResultsContainer = document.getElementById('search-results');
    const mainNavContainer = document.querySelector('.section-nav');
    const miniSearch = new MiniSearch({{ fields: ['title', 'content'], storeFields: ['title', 'id'], idField: 'id' }});
    try {{
        const response = await fetch('{SEARCH_INDEX_FILE}');
        const searchData = await response.json();
        miniSearch.addAll(searchData);
        console.log("✓ Поисковый индекс MiniSearch успешно загружен.");
    }} catch (error) {{
        console.error("Ошибка загрузки поискового индекса:", error);
        searchInput.placeholder = "Ошибка поиска";
        searchInput.disabled = true;
    }}
    const resetSearch = () => {{
        searchInput.value = '';
        searchResultsContainer.style.display = 'none';
        searchResultsContainer.innerHTML = '';
        mainNavContainer.style.display = 'block';
    }};
    searchInput.addEventListener('input', (e) => {{
        const query = e.target.value.trim();
        if (query.length < 2) {{
            searchResultsContainer.style.display = 'none';
            mainNavContainer.style.display = 'block';
            searchResultsContainer.innerHTML = '';
            return;
        }}
        const results = miniSearch.search(query, {{ prefix: true, fuzzy: 0.2 }});
        mainNavContainer.style.display = 'none';
        searchResultsContainer.style.display = 'block';
        searchResultsContainer.innerHTML = '';
        if (results.length > 0) {{
            const resultList = document.createElement('ul');
            resultList.className = 'search-results-list';
            results.slice(0, 10).forEach(doc => {{
                const li = document.createElement('li');
                const a = document.createElement('a');
                a.href = `#${{doc.id}}`; a.className = 'search-result-link'; a.textContent = doc.title;
                a.addEventListener('click', (event) => {{
                    event.preventDefault();
                    switchSection(doc.id);
                    window.location.hash = doc.id;
                    resetSearch();
                    // <<< ДОБАВЛЕНИЕ: ЗАКРЫВАЕМ МЕНЮ ПОСЛЕ КЛИКА НА МОБИЛЬНЫХ >>>
                    document.body.classList.remove('sidebar-is-open');
                }});
                li.appendChild(a);
                resultList.appendChild(li);
            }});
            searchResultsContainer.appendChild(resultList);
        }} else {{
            searchResultsContainer.innerHTML = '<p class="search-no-results">Ничего не найдено</p>';
        }}
    }});

    // --- <<< НОВЫЙ БЛОК: УПРАВЛЕНИЕ МОБИЛЬНЫМ МЕНЮ >>> ---
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const mobileOverlay = document.querySelector('.mobile-overlay');

    const toggleMobileMenu = () => {{
        document.body.classList.toggle('sidebar-is-open');
    }};

    mobileMenuToggle.addEventListener('click', toggleMobileMenu);
    mobileOverlay.addEventListener('click', toggleMobileMenu);

    // Закрываем меню после клика по ссылке в навигации
    document.querySelectorAll('.section-nav-link').forEach(link => {{
        link.addEventListener('click', () => {{
            if (document.body.classList.contains('sidebar-is-open')) {{
                document.body.classList.remove('sidebar-is-open');
            }}
        }});
    }});
    // --- <<< КОНЕЦ НОВОГО БЛОКА >>> ---

    // 7. ФУНКЦИЯ ПЕРЕКЛЮЧЕНИЯ СЕКЦИЙ (старый номер 6)
    const switchSection = (sectionId) => {{
        // ... (код этой функции остается без изменений) ...
        document.querySelectorAll('.content-section.is-active').forEach(s => s.classList.remove('is-active'));
        document.querySelectorAll('.content-section').forEach(s => s.style.display = 'none');
        document.querySelectorAll('.toc-container > .toc').forEach(t => t.style.display = 'none');
        const activeSection = document.getElementById(sectionId);
        const activeToc = document.getElementById(`toc-${{sectionId}}`);
        if (activeSection) {{
            activeSection.style.display = 'block';
            setTimeout(() => activeSection.classList.add('is-active'), 10);
        }}
        if (activeToc) activeToc.style.display = 'block';
        document.querySelectorAll('.section-nav-link').forEach(link => link.classList.remove('active'));
        const activeLink = document.querySelector(`.section-nav-link[data-section='${{sectionId}}']`);
        if (activeLink) activeLink.classList.add('active');
        document.querySelectorAll('.nav-list > li.is-open').forEach(li => li.classList.remove('is-open'));
        let current = activeLink;
        while(current){{
            if (current.tagName === 'LI' && current.parentElement.classList.contains('nav-list')) {{
                 if (current.querySelector('.nav-category-toggle')) {{
                    current.classList.add('is-open');
                 }}
            }}
            current = current.parentElement;
        }}
        document.querySelector('.page-container').scrollTop = 0;
        setupIntersectionObserver(sectionId);
    }};

    // 8. ИНИЦИАЛИЗАЦИЯ ПРИ ЗАГРУЗКЕ (старый номер 7)
    // ... (код этой функции остается без изменений) ...
    document.querySelectorAll('.section-nav-link').forEach(link => {{
        link.addEventListener('click', (e) => {{
            e.preventDefault();
            const sectionId = e.currentTarget.dataset.section;
            switchSection(sectionId);
            window.location.hash = sectionId;
        }});
    }});
    const initialSectionId = window.location.hash.substring(1);
    const firstSectionLink = document.querySelector('.section-nav-link');
    if (initialSectionId && document.getElementById(initialSectionId)) {{
        switchSection(initialSectionId);
    }} else if (firstSectionLink) {{
        switchSection(firstSectionLink.dataset.section);
    }}
}});
</script>
"""
# <<< ЗАМЕНИТЕ ВАШУ ФУНКЦИЮ create_html_page >>>
def create_html_page(title, style, section_nav_html, tocs_container_html, content_sections_html, script):
    """Собирает финальную HTML-страницу (версия с адаптацией)."""
    return f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>{style}</style>
</head>
<body>
    <!-- Оверлей для затемнения контента при открытом меню на мобильных -->
    <div class="mobile-overlay"></div>

    <aside class="sidebar">
        <div>
            <div class="sidebar-header">
                <div class="logo">{PAGE_LOGO_TEXT}</div>
            </div>
            
            <div class="search-container">
                {SEARCH_ICON_SVG}
                <input type="text" id="search-input" placeholder="Поиск по заметкам...">
            </div>
            
            <nav class="section-nav">
                {section_nav_html}
            </nav>
            
            <div id="search-results" style="display: none;"></div>
        </div>
        
        <div>
            <div class="toc-container">
                <p class="nav-title">На этой странице</p>
                {tocs_container_html}
            </div>
            <div class="theme-switch-wrapper">
                <span class="theme-switch-label">Тёмная тема</span>
                <label class="theme-switch" for="theme-toggle">
                    <input type="checkbox" id="theme-toggle" />
                    <span class="slider"></span>
                </label>
            </div>
        </div>
    </aside>

    <div class="page-container">
        <!-- Шапка для мобильных устройств -->
        <header class="mobile-header">
            <button class="mobile-menu-toggle" aria-label="Открыть меню">
                {MENU_ICON_SVG}
            </button>
            <div class="mobile-logo">{PAGE_LOGO_TEXT}</div>
        </header>
        <main class="main-content">
            {content_sections_html}
        </main>
    </div>

    {script}
</body>

</html>
    """
def process_blocks(soup):
    """Обрабатывает специальные блоки: уведомления, цитаты, аккорды."""
    # 1. Уведомления и цитаты (этот блок остается без изменений)
    admonition_types = ['note', 'tip', 'warning', 'danger']
    for blockquote in list(soup.find_all('blockquote')):
        p_tag = blockquote.find('p')
        if not p_tag: continue
        strong_tag = p_tag.find('strong')
        is_admonition = False
        if strong_tag:
            title_text_raw = strong_tag.get_text(strip=True)
            title_type = title_text_raw.lower().replace(':', '')
            if title_type in admonition_types:
                is_admonition = True
                admonition_div = soup.new_tag('div', **{'class': f'admonition {title_type}'})
                title_p = soup.new_tag('p', **{'class': 'admonition-title'})
                title_p.string = title_text_raw.replace(':', '').capitalize()
                admonition_div.append(title_p)
                strong_tag.decompose()
                while blockquote.contents:
                    element = blockquote.contents[0].extract()
                    admonition_div.append(element)
                blockquote.replace_with(admonition_div)
        if not is_admonition:
            text_content = p_tag.get_text(strip=True)
            if text_content.startswith('«') and text_content.endswith('»'):
                existing_classes = blockquote.get('class', [])
                blockquote['class'] = existing_classes + ['quote-block']

    # 2. НОВЫЙ ОБРАБОТЧИК АККОРДОВ И ТЕКСТА
    # Он ищет блоки ```chords-lyrics
    for pre_tag in list(soup.select('pre > code.language-chords')):
        # Создаем главный контейнер для всего блока песни
        song_part_div = soup.new_tag('div', **{'class': 'song-part'})
        
        # Получаем сырой текст, сохраняя переносы строк
        lines = pre_tag.get_text().splitlines()
        
        # Регулярное выражение для поиска аккордов. Упрощено для надежности.
        # Ищет последовательности из букв, цифр, #, b, /, которые не являются обычными словами.
        chord_regex = re.compile(r'([A-G][#b]?(?:maj|min|m|sus|dim|aug|add|M|º|ø|\+|-|7|9|11|13|6|5|4|2|b5|\#5)*\/?(?:[A-G][#b]?)?)')

        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Если строка пустая, добавляем пустой параграф для отступа
            if not line.strip():
                song_part_div.append(soup.new_tag('p', **{'class': 'song-empty-line'}))
                i += 1
                continue

            # Если строка - это заголовок секции (например, [Verse 1])
            if line.strip().startswith('[') and line.strip().endswith(']'):
                section_p = soup.new_tag('p', **{'class': 'song-section-title'})
                section_p.string = line.strip()
                song_part_div.append(section_p)
                i += 1
                continue

            # Проверяем, является ли текущая строка строкой с аккордами
            # Критерий: более 50% "слов" в строке являются аккордами.
            words = line.split()
            chord_count = sum(1 for word in words if chord_regex.fullmatch(word))
            is_chord_line = len(words) > 0 and (chord_count / len(words)) > 0.5
            
            if is_chord_line and i + 1 < len(lines):
                # Это строка аккордов, и за ней есть строка текста
                lyrics_line = lines[i+1]
                
                line_pair_div = soup.new_tag('div', **{'class': 'line-pair'})
                
                # ИЗМЕНЕНИЕ: Добавляем класс 'no-copy-button'
                chords_pre = soup.new_tag('pre', **{'class': 'chords-line no-copy-button'})
                current_pos = 0
                for match in chord_regex.finditer(line):
                    chords_pre.append(line[current_pos:match.start()])
                    chord_span = soup.new_tag('span', **{'class': 'chord'})
                    chord_span.string = match.group(1)
                    chords_pre.append(chord_span)
                    current_pos = match.end()
                line_pair_div.append(chords_pre)
                
                # ИЗМЕНЕНИЕ: Добавляем класс 'no-copy-button'
                lyrics_pre = soup.new_tag('pre', **{'class': 'lyrics-line no-copy-button'})
                lyrics_pre.string = lyrics_line
                line_pair_div.append(lyrics_pre)
                
                song_part_div.append(line_pair_div)
                
                i += 2
            else:
                # ИЗМЕНЕНИЕ: Добавляем класс 'no-copy-button'
                lyrics_pre = soup.new_tag('pre', **{'class': 'lyrics-line-only no-copy-button'})
                lyrics_pre.string = line
                song_part_div.append(lyrics_pre)
                i += 1
        
        pre_tag.parent.replace_with(song_part_div)

    return soup
    
# <<< ОБНОВЛЕННАЯ ВЕРСИЯ get_clean_title >>>
def get_clean_title(name):
    """Превращает '01-My-Song.md' в 'My Song', сохраняя регистр."""
    base_name = os.path.splitext(name)[0]
    clean_name = re.sub(r'^\d+[-_]', '', base_name).replace('-', ' ').replace('_', ' ')
    return clean_name.strip()

def main():
    if not os.path.isdir(INPUT_MD_DIR) or not os.path.exists(CSS_FILE):
        print(f"Ошибка: Убедитесь, что папка '{INPUT_MD_DIR}' и файл '{CSS_FILE}' существуют.")
        return

    print("Генерация сайта с поиском...")

    with open(CSS_FILE, 'r', encoding='utf-8') as f:
        css_styles = f.read()

    nav_tree = {}
    content_sections = []
    tocs_containers = []
    search_index_data = [] # <<< НОВЫЙ СПИСОК ДЛЯ ИНДЕКСА

    for root, dirs, files in os.walk(INPUT_MD_DIR, topdown=True):
        dirs.sort()
        files.sort()
        
        path_parts = os.path.relpath(root, INPUT_MD_DIR).split(os.sep)
        if path_parts[0] == '.': path_parts = []
        
        current_level_dict = nav_tree
        for part in path_parts:
            current_level_dict = current_level_dict.setdefault(part, {'children': {}})['children']
        
        for filename in files:
            if not filename.endswith('.md'):
                continue
            
            clean_title = get_clean_title(filename) # <<< ПОЛУЧАЕМ ЧИСТОЕ ИМЯ
            full_path = os.path.join(root, filename)
            relative_path = os.path.relpath(full_path, INPUT_MD_DIR)
            slug_base = os.path.splitext(relative_path.replace(os.sep, '-'))[0]
            section_slug = f"section-{slugify(re.sub(r'^\d+[-_]', '', slug_base))}"
            
            current_level_dict[filename] = { 'type': 'file', 'slug': section_slug }

            print(f"-> Обработка: {full_path}")
            with open(full_path, 'r', encoding='utf-8') as f: md_text = f.read()

            html_content = markdown.markdown(md_text, extensions=['fenced_code', 'tables'])
            soup = BeautifulSoup(html_content, 'html.parser')
            soup = process_blocks(soup)     
            
            # Стало:
            # Добавляем кнопки "Копировать" только в блоки кода, ИСКЛЮЧАЯ те, что для аккордов
            for pre_tag in soup.select('pre:not(.no-copy-button)'):
                button_tag = soup.new_tag('button', **{'class': 'copy-button'})
                button_tag.append(BeautifulSoup(COPY_ICON_SVG, 'html.parser'))
                button_tag.append(" Копировать")
                pre_tag.insert(0, button_tag)
            
            toc_items = []
            for header in soup.find_all(['h2', 'h3']):
                header_text = header.get_text()
                header_id = f"{section_slug}-{slugify(header_text)}"
                header['id'] = header_id
                level = int(header.name[1])
                toc_items.append(f'<li class="toc-level-{level}"><a href="#{header_id}">{header_text}</a></li>')

            display_style = 'style="display: none;"'
            toc_html = f'<ul class="toc" id="toc-{section_slug}" {display_style}>' + "\n".join(toc_items) + '</ul>'
            tocs_containers.append(toc_html)
            
            content_section_html = f'<div class="content-section" id="{section_slug}" {display_style}>{str(soup)}</div>'
            content_sections.append(content_section_html)

            # <<< НОВЫЙ БЛОК: ДОБАВЛЕНИЕ ДАННЫХ В ПОИСКОВЫЙ ИНДЕКС >>>
            # Используем исходный Markdown-текст для индексации, т.к. он чище, чем HTML
            search_index_data.append({
                'id': section_slug,
                'title': clean_title,
                'content': md_text
            })

    # Сохраняем поисковый индекс в JSON файл
    with open(SEARCH_INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(search_index_data, f, ensure_ascii=False, indent=2)
    print(f"✓ Поисковый индекс сохранен в {SEARCH_INDEX_FILE}")

    def build_nav_html(tree):
        html = '<ul class="nav-list">'
        sorted_items = sorted(tree.items(), key=lambda x: ('children' not in x[1], x[0]))
        for name, data in sorted_items:
            clean_name = get_clean_title(name)
            if 'children' in data:
                html += f'<li><div class="nav-category-toggle">{CHEVRON_RIGHT_SVG}<span>{clean_name}</span></div>'
                html += build_nav_html(data['children'])
                html += '</li>'
            else:
                html += f'<li><a href="#" class="section-nav-link" data-section="{data["slug"]}">{clean_name}</a></li>'
        html += '</ul>'
        return html

    section_nav_html = build_nav_html(nav_tree)
    print("✓ Дерево навигации построено.")

    final_html = create_html_page(
        title=SITE_TITLE,
        style=css_styles,
        section_nav_html=section_nav_html,
        tocs_container_html="\n".join(tocs_containers),
        content_sections_html="\n".join(content_sections),
        script=JAVASCRIPT_CODE
    )
    print("✓ Собрана финальная HTML-страница.")

    with open(OUTPUT_HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(final_html)
    print(f"\nГотово! Результат в файле: {os.path.abspath(OUTPUT_HTML_FILE)}")


if __name__ == '__main__':
    main()