PYTHON ?= python

run:  ## повний прогін: усі моделі × конфіги семплінгу → results/
	$(PYTHON) main.py run

smoke:  ## швидка перевірка на 3 текстах лише провайдерською моделлю
	$(PYTHON) main.py run --models provider --sampling A --limit 3

test:
	$(PYTHON) -m pytest -q

.PHONY: run smoke test
