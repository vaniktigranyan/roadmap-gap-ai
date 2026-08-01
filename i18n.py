TRANSLATIONS = {
    'en': {
        # ---- Hero ----
        'main_header': '🕵️ The Silent Stakeholder',
        'hero_sub': 'Latent needs users never stated outright — and how long the roadmap took to '
                    'answer them, if it ever did. Every number traces back to specific reviews.',
        'hero_meta': 'Roadmap: {issues} issues · User signals: {reviews} app reviews',


        # ---- Hero (new) ----
        'hero_eyebrow': 'Roadmap × Reviews · Latent need discovery',
        'hero_title_a': 'The needs users ',
        'hero_title_b': 'never said out loud',
        'hero_roadmap': 'Roadmap',
        'hero_signals': 'User signals',
        'hero_reviews_word': 'reviews',
        'hero_considered': 'Considered',
        'hero_candidates_word': 'candidate needs',

        # ---- Response-latency timeline ----
        'stat_never': 'Never framed at all',
        'stat_worst_latency': 'Longest silence',
        'tl_users_spoke': 'Users spoke',
        'tl_roadmap_answered': 'Roadmap answered',
        'tl_users_voiced': '{n} reviews said it',
        'tl_never': 'NEVER',
        'tl_no_ticket': 'No ticket, ever',
        'tl_closest_only': 'nearest ticket #{number} is only {sim} similar',
        'tl_roadmap_silent': 'roadmap silent',
        'tl_opened_still_open': '#{number} opened · still open today',
        'tl_resolved_in': '#{number} opened · then took {span} to close',
        'tl_declined': '#{number} opened · closed as not planned',

        # ---- Summary strip ----
        'stat_needs': 'Unmet needs surfaced',
        'stat_cited': 'Reviews cited as evidence',
        'stat_verdicts': 'Verdict mix',
        'stat_upheld': 'Upheld by the panel',

        # ---- Panel rulings ----
        'ruling_upheld': 'UPHELD',
        'ruling_contested': 'CONTESTED',
        'ruling_overturned': 'OVERTURNED',
        'panel_gap_n': 'Need #{n}',
        'panel_must_prepare': 'Be ready to answer',
        'panel_disputes': 'Unresolved between panellists',
        'panel_transcript': 'Full transcript',
        'panel_none': 'No panel review has been run yet. Run `python run_debate.py` to audit these results.',
        'panel_stale': 'The stored panel review predates the current results — re-run `python run_debate.py`.',
        'round_n': 'Round {n}',
        'phase_opening': 'Opening statements',
        'phase_cross': 'Cross-examination',
        'phase_interrogation': 'The judge interrogates',
        'phase_rebuttal': 'Answering the judge',
        'phase_ruling': 'Ruling',

        # ---- Panel roles + raw-data column headers ----
        'agent_user_advocate': 'User Advocate',
        'agent_roadmap_owner': 'Roadmap Owner',
        'agent_evidence_auditor': 'Evidence Auditor',
        'agent_judge': 'Judge',
        'col_number': 'Issue #',
        'col_title': 'Title',
        'col_state': 'State',
        'col_state_reason': 'Closed as',
        'col_milestone_title': 'Milestone',
        'col_cluster': 'Functional area',
        'col_reactions_plus1': '👍 reactions',
        'col_html_url': 'Link',
        'col_id': 'Review ID',
        'col_star': 'Stars',
        'col_review_date': 'Date',
        'col_review_text': 'Review',
        'col_open_issues': 'Open issues',
        'col_closed_issues': 'Closed issues',
        'col_due_on': 'Due',

        # ---- Sidebar ----
        'product_label': '📦 Product',
        'product_help': 'Any app with both a large review corpus and a public GitHub roadmap. '
                        'Run `python discover_projects.py` to refresh the catalogue.',
        'sidebar_roadmap': 'Roadmap:',
        'sidebar_signals': 'Signals:',
        'product_ready': '✅ Analysed — {n} needs below',
        'product_not_analysed': '⚠️ Not analysed yet — press Re-run analysis',
        'hero_product': 'Product',
        'language_label': '🌐 Language',
        'advanced_mode': '🔬 Analyst mode',
        'advanced_mode_help': 'Show the full audit trail: every candidate considered, the shared '
                              'taxonomy, the adversarial debate, and raw data.',
        'sidebar_caption': 'Re-fetch GitHub + reviews and rerun the whole analysis.',
        'run_button': '🔄 Re-run analysis',
        'no_analysis_yet': 'No analysis yet. Open the sidebar and click **Re-run analysis** to start.',

        # ---- Top needs ----
        'top_needs_header': 'Top unmet needs',
        'top_needs_caption': 'Ranked by strength of evidence. Every claim traces back to specific review '
                             'IDs and to what the roadmap did — or never did — about it.',
        'confidence_label': 'Confidence',

        # Verdict — short (badge)
        'verdict_short_ignored': 'IGNORED',
        'verdict_short_underprioritized': 'UNDER-PRIORITIZED',
        'verdict_short_misunderstood': 'MISUNDERSTOOD',
        'verdict_short_covered': 'COVERED',

        # Verdict — full (explained)
        'verdict_ignored': 'IGNORED — no roadmap issue addresses this',
        'verdict_underprioritized': 'UNDER-PRIORITIZED — an issue exists but is stale or unscheduled',
        'verdict_misunderstood': 'MISUNDERSTOOD — an issue exists but is framed around a different problem',
        'verdict_covered': 'COVERED — the roadmap already fully addresses this',

        # Chips
        'chip_users': 'Users signalling',
        'chip_share': 'Of corpus',
        'chip_avg_rating': 'Avg rating',
        'chip_roadmap': 'Roadmap',
        'chip_no_issue': 'no match',

        # Evidence + scoring
        'evidence_trace': '📋 Evidence · {n} reviews',
        'why_this_score': '📊 Why this score',
        'evidence_volume': 'Evidence volume',
        'evidence_volume_help': 'How many independent reviews back this need (log-normalized)',
        'rating_spread': 'Rating spread',
        'rating_spread_help': 'Signal comes from varied ratings, not just angry 1★ venting',
        'consistency': 'Consistency',
        'consistency_help': 'How semantically tight the supporting reviews are with each other',
        'gap_certainty': 'Roadmap gap certainty',
        'gap_certainty_help': 'How clear-cut the roadmap failure is, dampened by evidence consistency',
        'why_latent': 'Why this is latent:',
        'roadmap_check': 'Roadmap check:',
        'closest_issue': '🔗 Roadmap issue: [#{number} {title}]({url}) · state: {state} · milestone: {milestone}',
        'closest_below_threshold': 'Closest issue considered: [#{number} {title}]({url}) — similarity '
                                   '{sim}, below the 0.4 match threshold. That is *why* the verdict is '
                                   'IGNORED, rather than simply "nothing exists".',
        'none_milestone': 'none',

        # ---- Chat ----
        'chat_header': '💬 Ask about this analysis',
        'chat_caption': 'Every answer is grounded in the actual data — review IDs, issue numbers and '
                        'confidence components, not guesses.',
        'chat_placeholder': 'e.g. How did you conclude need #1? How many users want it?',
        'chat_q1': 'Why is #1 ranked first?',
        'chat_q2': 'How many users signal need #1?',
        'chat_q3': 'What gaps did you rule out, and why?',
        'chat_thinking': 'Reading the evidence...',
        'chat_clear': 'Clear conversation',
        'chat_error': 'Could not answer: {error}',

        # ---- Analyst mode ----
        'adv_header': 'Analyst mode',
        'adv_caption': 'The full audit trail behind the five needs above.',
        'adv_tab_candidates': 'All candidates',
        'adv_tab_clusters': 'Functional areas',
        'adv_tab_debate': 'Adversarial review',
        'adv_tab_raw': 'Raw data',

        'candidates_caption': 'Every latent need the system found — including those ranked below the '
                              'top 5 and those excluded because the roadmap already covers them.',
        'candidates_col_need': 'Need',
        'candidates_col_verdict': 'Verdict',
        'candidates_col_confidence': 'Confidence',
        'candidates_col_top5': 'Top 5',
        'candidates_col_evidence_count': 'Reviews',
        'candidates_col_matched_issue': 'Issue',

        'clusters_caption': 'A shared taxonomy built by embedding and clustering roadmap issues and '
                            'user reviews together — this is what makes the two sides comparable.',
        'chart_issues': 'Roadmap issues',
        'chart_reviews': 'Reviews',
        'chart_count_axis': 'Count',

        'debate_header': 'Four agents audited these results',
        'debate_caption': 'A User Advocate, a Roadmap Owner and an Evidence Auditor argued over the full '
                          'analysis across five rounds while a Judge cross-examined them. This panel has '
                          'already caught two real methodology bugs, both since fixed.',
        'debate_top5_valid': 'Top-5 valid',
        'debate_conf_justified': 'Confidence justified',
        'debate_verdicts_sound': 'Verdicts sound',

        'tab_issues': 'Issues',
        'tab_reviews': 'Reviews',
        'tab_milestones': 'Milestones',

        # ---- Pipeline run feedback ----
        'run_status_title': 'Analysing {product}…',
        'run_status_done': '✅ {product} analysed',
        'run_status_failed': '❌ Analysis failed: {error}',
        'run_github': 'Connecting to GitHub — {repo}',
        'run_github_milestones': 'Found {n} milestones · now loading issues from {repo}',
        'run_github_paging': 'Loading roadmap from {repo} — {n} items so far…',
        'run_github_done': 'Roadmap loaded — {n} issues',
        'run_reviews': 'Downloading user reviews for {package}…',
        'run_reviews_done': 'Reviews loaded — {n} of them',
        'run_no_reviews': 'No reviews found for {package} in the dataset — nothing to analyse',
        'run_saving_sources': 'Storing both sides in the database…',
        'run_saving_results': 'Saving the results…',
        'run_done': 'Done — {n} unmet needs surfaced',
        'run_success': 'Surfaced {n} unmet needs for {product}.',
        'run_show_results': 'Show the results',

        # ---- Pipeline status ----
        'status_fetching_github': '📥 Fetching GitHub issues + milestones...',
        'status_fetching_reviews': '📥 Fetching reviews from the HuggingFace dataset...',
        'status_clustering': '🧠 Clustering and mining latent needs...',
        'status_saving': '💾 Saving results...',
        'status_done': '✅ Done',

        'footer': 'Silent Stakeholder — latent need discovery by cross-analyzing a product\'s '
                  'GitHub roadmap against its real app reviews',
    },

    'ru': {
        # ---- Hero ----
        'main_header': '🕵️ Молчаливый стейкхолдер',
        'hero_sub': 'Скрытые потребности, о которых пользователи прямо не сказали — и сколько лет '
                    'roadmap шёл к ним, если дошёл вообще. Каждое число ведёт к конкретным отзывам.',
        'hero_meta': 'Roadmap: {issues} issues · Сигналы пользователей: {reviews} отзывов',


        # ---- Hero (new) ----
        'hero_eyebrow': 'Roadmap × Отзывы · Поиск скрытых потребностей',
        'hero_title_a': 'То, о чём пользователи ',
        'hero_title_b': 'молчали',
        'hero_roadmap': 'Roadmap',
        'hero_signals': 'Сигналы пользователей',
        'hero_reviews_word': 'отзывов',
        'hero_considered': 'Рассмотрено',
        'hero_candidates_word': 'кандидатов',

        # ---- Response-latency timeline ----
        'stat_never': 'Так и не оформлено',
        'stat_worst_latency': 'Дольше всего молчали',
        'tl_users_spoke': 'Пользователи сказали',
        'tl_roadmap_answered': 'Roadmap ответил',
        'tl_users_voiced': 'об этом писали в {n} отзывах',
        'tl_never': 'НИКОГДА',
        'tl_no_ticket': 'Тикета так и не было',
        'tl_closest_only': 'ближайший тикет #{number} схож лишь на {sim}',
        'tl_roadmap_silent': 'roadmap молчал',
        'tl_opened_still_open': '#{number} открыт · до сих пор открыт',
        'tl_resolved_in': '#{number} открыт · закрывали ещё {span}',
        'tl_declined': '#{number} открыт · закрыт как «не планируется»',

        # ---- Summary strip ----
        'stat_needs': 'Найдено потребностей',
        'stat_cited': 'Отзывов в доказательствах',
        'stat_verdicts': 'Состав вердиктов',
        'stat_upheld': 'Подтверждено панелью',

        # ---- Panel rulings ----
        'ruling_upheld': 'ПОДТВЕРЖДЕНО',
        'ruling_contested': 'ОСПОРЕНО',
        'ruling_overturned': 'ОТКЛОНЕНО',
        'panel_gap_n': 'Потребность №{n}',
        'panel_must_prepare': 'Готовьтесь ответить на',
        'panel_disputes': 'Осталось нерешённым между экспертами',
        'panel_transcript': 'Полная стенограмма',
        'panel_none': 'Разбор панелью ещё не проводился. Запустите `python run_debate.py`.',
        'panel_stale': 'Сохранённый разбор относится к прежним результатам — перезапустите `python run_debate.py`.',
        'round_n': 'Раунд {n}',
        'phase_opening': 'Вступительные позиции',
        'phase_cross': 'Перекрёстный разбор',
        'phase_interrogation': 'Судья задаёт вопросы',
        'phase_rebuttal': 'Ответы судье',
        'phase_ruling': 'Решение',

        # ---- Panel roles + raw-data column headers ----
        'agent_user_advocate': 'Адвокат пользователей',
        'agent_roadmap_owner': 'Владелец roadmap',
        'agent_evidence_auditor': 'Аудитор доказательств',
        'agent_judge': 'Судья',
        'col_number': '№ issue',
        'col_title': 'Заголовок',
        'col_state': 'Статус',
        'col_state_reason': 'Как закрыт',
        'col_milestone_title': 'Milestone',
        'col_cluster': 'Функциональная зона',
        'col_reactions_plus1': '👍 реакций',
        'col_html_url': 'Ссылка',
        'col_id': 'ID отзыва',
        'col_star': 'Оценка',
        'col_review_date': 'Дата',
        'col_review_text': 'Текст отзыва',
        'col_open_issues': 'Открытых issues',
        'col_closed_issues': 'Закрытых issues',
        'col_due_on': 'Срок',

        # ---- Sidebar ----
        'product_label': '📦 Продукт',
        'product_help': 'Любое приложение, у которого есть и большой корпус отзывов, и публичный '
                        'GitHub-роадмап. Обновить список: `python discover_projects.py`.',
        'sidebar_roadmap': 'Roadmap:',
        'sidebar_signals': 'Сигналы:',
        'product_ready': '✅ Проанализировано — {n} потребностей ниже',
        'product_not_analysed': '⚠️ Ещё не анализировали — нажмите «Перезапустить анализ»',
        'hero_product': 'Продукт',
        'language_label': '🌐 Язык',
        'advanced_mode': '🔬 Режим аналитика',
        'advanced_mode_help': 'Показать полную цепочку аудита: все рассмотренные кандидаты, общую '
                              'таксономию, спор агентов и исходные данные.',
        'sidebar_caption': 'Заново загрузить GitHub и отзывы и пересчитать весь анализ.',
        'run_button': '🔄 Перезапустить анализ',
        'no_analysis_yet': 'Анализ ещё не запущен. Откройте боковую панель и нажмите '
                           '**Перезапустить анализ**.',

        # ---- Top needs ----
        'top_needs_header': 'Главные неудовлетворённые потребности',
        'top_needs_caption': 'Отсортированы по силе доказательств. Каждое утверждение прослеживается до '
                             'конкретных отзывов и до того, что roadmap с этим сделал — или не сделал.',
        'confidence_label': 'Уверенность',

        # Verdict — short (badge)
        'verdict_short_ignored': 'ИГНОРИРУЕТСЯ',
        'verdict_short_underprioritized': 'НЕДООЦЕНЕНО',
        'verdict_short_misunderstood': 'ПОНЯТО НЕВЕРНО',
        'verdict_short_covered': 'ПОКРЫТО',

        # Verdict — full (explained)
        'verdict_ignored': 'ИГНОРИРУЕТСЯ — в roadmap нет issue про это',
        'verdict_underprioritized': 'НЕДООЦЕНЕНО — issue есть, но заброшен или не запланирован',
        'verdict_misunderstood': 'ПОНЯТО НЕВЕРНО — issue есть, но решает другую задачу',
        'verdict_covered': 'ПОКРЫТО — roadmap уже полностью закрывает это',

        # Chips
        'chip_users': 'Пользователей',
        'chip_share': 'От корпуса',
        'chip_avg_rating': 'Средняя оценка',
        'chip_roadmap': 'Roadmap',
        'chip_no_issue': 'нет совпадения',

        # Evidence + scoring
        'evidence_trace': '📋 Доказательства · {n} отзывов',
        'why_this_score': '📊 Откуда эта оценка',
        'evidence_volume': 'Объём доказательств',
        'evidence_volume_help': 'Сколько независимых отзывов подтверждают потребность (лог-шкала)',
        'rating_spread': 'Разброс оценок',
        'rating_spread_help': 'Сигнал идёт от разных оценок, а не только от злых 1★',
        'consistency': 'Согласованность',
        'consistency_help': 'Насколько подтверждающие отзывы близки друг к другу по смыслу',
        'gap_certainty': 'Чёткость пробела',
        'gap_certainty_help': 'Насколько однозначен провал roadmap, с поправкой на согласованность',
        'why_latent': 'Почему это скрытая потребность:',
        'roadmap_check': 'Проверка по roadmap:',
        'closest_issue': '🔗 Issue из roadmap: [#{number} {title}]({url}) · статус: {state} · '
                         'milestone: {milestone}',
        'closest_below_threshold': 'Ближайший рассмотренный issue: [#{number} {title}]({url}) — схожесть '
                                   '{sim}, ниже порога совпадения 0.4. Именно *поэтому* вердикт '
                                   'ИГНОРИРУЕТСЯ, а не просто «ничего нет».',
        'none_milestone': 'нет',

        # ---- Chat ----
        'chat_header': '💬 Спросите об этом анализе',
        'chat_caption': 'Каждый ответ опирается на реальные данные — ID отзывов, номера issue и '
                        'компоненты уверенности, а не на догадки.',
        'chat_placeholder': 'Например: как вы пришли к потребности №1? Сколько пользователей её хотят?',
        'chat_q1': 'Почему №1 на первом месте?',
        'chat_q2': 'Сколько пользователей сигналят о №1?',
        'chat_q3': 'Какие пробелы вы отбросили и почему?',
        'chat_thinking': 'Читаю доказательства...',
        'chat_clear': 'Очистить диалог',
        'chat_error': 'Не удалось ответить: {error}',

        # ---- Analyst mode ----
        'adv_header': 'Режим аналитика',
        'adv_caption': 'Полная цепочка аудита за пятью потребностями выше.',
        'adv_tab_candidates': 'Все кандидаты',
        'adv_tab_clusters': 'Функциональные зоны',
        'adv_tab_debate': 'Спор агентов',
        'adv_tab_raw': 'Исходные данные',

        'candidates_caption': 'Все скрытые потребности, которые нашла система — включая те, что не '
                              'вошли в топ-5, и те, что исключены, потому что roadmap их уже покрывает.',
        'candidates_col_need': 'Потребность',
        'candidates_col_verdict': 'Вердикт',
        'candidates_col_confidence': 'Уверенность',
        'candidates_col_top5': 'Топ-5',
        'candidates_col_evidence_count': 'Отзывов',
        'candidates_col_matched_issue': 'Issue',

        'clusters_caption': 'Общая таксономия, построенная совместной кластеризацией issues и отзывов — '
                            'именно она делает две стороны сопоставимыми.',
        'chart_issues': 'Issues в roadmap',
        'chart_reviews': 'Отзывы',
        'chart_count_axis': 'Количество',

        'debate_header': 'Четыре агента проверили эти результаты',
        'debate_caption': 'Адвокат пользователей, Владелец roadmap и Аудитор доказательств спорили обо '
                          'всём анализе пять раундов, а Судья вёл перекрёстный допрос. Панель уже нашла '
                          'две реальные ошибки в методологии — обе исправлены.',
        'debate_top5_valid': 'Топ-5 валиден',
        'debate_conf_justified': 'Уверенность обоснована',
        'debate_verdicts_sound': 'Вердикты корректны',

        'tab_issues': 'Issues',
        'tab_reviews': 'Отзывы',
        'tab_milestones': 'Milestones',

        # ---- Pipeline run feedback ----
        'run_status_title': 'Анализирую {product}…',
        'run_status_done': '✅ {product} проанализирован',
        'run_status_failed': '❌ Анализ не удался: {error}',
        'run_github': 'Подключаюсь к GitHub — {repo}',
        'run_github_milestones': 'Найдено {n} milestones · загружаю issues из {repo}',
        'run_github_paging': 'Загружаю roadmap из {repo} — уже {n} элементов…',
        'run_github_done': 'Roadmap загружен — {n} issues',
        'run_reviews': 'Скачиваю отзывы пользователей для {package}…',
        'run_reviews_done': 'Отзывы загружены — {n} штук',
        'run_no_reviews': 'Для {package} в датасете нет отзывов — анализировать нечего',
        'run_saving_sources': 'Сохраняю обе стороны в базу…',
        'run_saving_results': 'Сохраняю результаты…',
        'run_done': 'Готово — найдено {n} неудовлетворённых потребностей',
        'run_success': 'Для {product} найдено {n} неудовлетворённых потребностей.',
        'run_show_results': 'Показать результаты',

        # ---- Pipeline status ----
        'status_fetching_github': '📥 Загружаю issues и milestones из GitHub...',
        'status_fetching_reviews': '📥 Загружаю отзывы из датасета HuggingFace...',
        'status_clustering': '🧠 Кластеризую и извлекаю скрытые потребности...',
        'status_saving': '💾 Сохраняю результаты...',
        'status_done': '✅ Готово',

        'footer': 'Silent Stakeholder — поиск скрытых потребностей сопоставлением GitHub roadmap '
                  'любого продукта с реальными отзывами на него',
    },
}


def get_text(lang: str, key: str, **kwargs) -> str:
    text = TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key) or TRANSLATIONS['en'].get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text
