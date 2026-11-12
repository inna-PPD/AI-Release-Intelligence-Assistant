PYTHON ?= python

run:  ## повний прогін: усі моделі × конфіги семплінгу → results/
	$(PYTHON) main.py run

smoke:  ## швидка перевірка на 3 текстах лише провайдерською моделлю
	$(PYTHON) main.py run --models provider --sampling A --limit 3

case2:  ## кейс 2: ingest → якість пошуку → evals відповідей (код 1, якщо метрика нижче порогу)
	$(PYTHON) main.py case2

ask:  ## кейс 2: make ask Q="питання"
	$(PYTHON) main.py ask "$(Q)"

test:
	$(PYTHON) -m pytest -q

.PHONY: run smoke case2 ask test
