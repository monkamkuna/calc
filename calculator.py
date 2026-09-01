from __future__ import annotations

import math
import re
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="Modern Calculator", version="1.0.0")


class CalculationRequest(BaseModel):
    expression: str


def _safe_calculate(expression: str) -> float:
    sanitized = expression.strip()
    if not sanitized:
        raise ValueError("Expression is empty")

    if not re.fullmatch(r"[0-9\s+\-*/().,%^]+", sanitized):
        raise ValueError("Expression contains unsupported characters")

    normalized = sanitized.replace("^", "**").replace("%", "/100")
    try:
        result = eval(normalized, {"__builtins__": {}}, {"math": math})
    except Exception as exc:  # pragma: no cover - defensive validation
        raise ValueError(f"Invalid expression: {exc}") from exc

    if isinstance(result, complex):
        raise ValueError("Complex numbers are not supported")

    return float(result)


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>Modern Calculator</title>
            <style>
                :root {
                    --bg-1: #0f172a;
                    --bg-2: #111827;
                    --panel: rgba(15, 23, 42, 0.78);
                    --panel-border: rgba(148, 163, 184, 0.18);
                    --screen: rgba(15, 118, 110, 0.2);
                    --screen-text: #ecfeff;
                    --primary: #8b5cf6;
                    --primary-dark: #7c3aed;
                    --secondary: #22c55e;
                    --accent: #38bdf8;
                    --muted: #cbd5e1;
                    --danger: #f87171;
                    --shadow: 0 25px 60px rgba(15, 23, 42, 0.45);
                }

                * { box-sizing: border-box; }

                body {
                    margin: 0;
                    min-height: 100vh;
                    display: grid;
                    place-items: center;
                    font-family: Inter, "Segoe UI", sans-serif;
                    background:
                        radial-gradient(circle at top, rgba(139, 92, 246, 0.25), transparent 30%),
                        linear-gradient(135deg, var(--bg-1) 0%, var(--bg-2) 100%);
                    color: white;
                }

                .calculator {
                    width: min(92vw, 420px);
                    background: var(--panel);
                    border: 1px solid var(--panel-border);
                    border-radius: 28px;
                    backdrop-filter: blur(16px);
                    box-shadow: var(--shadow);
                    padding: 22px;
                }

                .display {
                    background: var(--screen);
                    border: 1px solid rgba(148, 163, 184, 0.16);
                    border-radius: 18px;
                    min-height: 120px;
                    padding: 18px 16px;
                    display: flex;
                    align-items: end;
                    justify-content: flex-end;
                    overflow: hidden;
                }

                #expression {
                    width: 100%;
                    border: none;
                    background: transparent;
                    text-align: right;
                    font-size: clamp(2rem, 4vw, 3rem);
                    color: var(--screen-text);
                    outline: none;
                    font-weight: 600;
                    letter-spacing: 0.04em;
                }

                .keys {
                    display: grid;
                    grid-template-columns: repeat(4, minmax(0, 1fr));
                    gap: 12px;
                    margin-top: 18px;
                }

                button {
                    border: none;
                    border-radius: 18px;
                    min-height: 64px;
                    font-size: 1.15rem;
                    font-weight: 700;
                    cursor: pointer;
                    transition: transform 0.15s ease, opacity 0.15s ease, box-shadow 0.2s ease;
                    box-shadow: inset 0 1px 0 rgba(255,255,255,0.08);
                }

                button:hover { transform: translateY(-1px); }
                button:active { transform: translateY(1px); }

                .btn-operator {
                    background: rgba(59, 130, 246, 0.18);
                    color: #bfdbfe;
                }

                .btn-action {
                    background: rgba(248, 113, 113, 0.16);
                    color: #fecaca;
                }

                .btn-number {
                    background: rgba(15, 23, 42, 0.9);
                    color: #f8fafc;
                }

                .btn-equals {
                    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
                    color: white;
                    grid-column: span 2;
                }

                .btn-zero {
                    grid-column: span 2;
                }
            </style>
        </head>
        <body>
            <main class="calculator" aria-label="Calculator app">
                <div class="display">
                    <input id="expression" type="text" inputmode="numeric" aria-label="Calculator display" />
                </div>

                <div class="keys">
                    <button class="btn-action" data-action="clear">C</button>
                    <button class="btn-action" data-action="delete">⌫</button>
                    <button class="btn-operator" data-value="%">%</button>
                    <button class="btn-operator" data-value="/">÷</button>

                    <button class="btn-number" data-value="7">7</button>
                    <button class="btn-number" data-value="8">8</button>
                    <button class="btn-number" data-value="9">9</button>
                    <button class="btn-operator" data-value="*">×</button>

                    <button class="btn-number" data-value="4">4</button>
                    <button class="btn-number" data-value="5">5</button>
                    <button class="btn-number" data-value="6">6</button>
                    <button class="btn-operator" data-value="-">−</button>

                    <button class="btn-number" data-value="1">1</button>
                    <button class="btn-number" data-value="2">2</button>
                    <button class="btn-number" data-value="3">3</button>
                    <button class="btn-operator" data-value="+">+</button>

                    <button class="btn-number btn-zero" data-value="0">0</button>
                    <button class="btn-number" data-value=".">.</button>
                    <button class="btn-equals" data-action="equals">=</button>
                </div>
            </main>

            <script>
                const display = document.getElementById('expression');
                let current = '';

                function updateDisplay() {
                    display.value = current;
                }

                function appendValue(value) {
                    const last = current.slice(-1);
                    if (['+', '-', '*', '/', '%'].includes(value) && ['+', '-', '*', '/', '%'].includes(last)) {
                        current = current.slice(0, -1) + value;
                    } else {
                        current += value;
                    }
                    updateDisplay();
                }

                function clearDisplay() {
                    current = '';
                    updateDisplay();
                }

                function deleteLast() {
                    current = current.slice(0, -1);
                    updateDisplay();
                }

                function evaluateExpression() {
                    try {
                        if (!current) return;
                        const sanitized = current.replace(/×/g, '*').replace(/÷/g, '/').replace(/−/g, '-');
                        const valid = /^[0-9+\\-*/%.()\\s]+$/.test(sanitized);
                        if (!valid) throw new Error('Invalid input');
                        const result = Function(`"use strict"; return (${sanitized});`)();
                        current = Number.isFinite(result) ? String(result) : 'Error';
                        updateDisplay();
                    } catch (error) {
                        current = 'Error';
                        updateDisplay();
                    }
                }

                document.querySelectorAll('[data-value]').forEach((button) => {
                    button.addEventListener('click', () => {
                        appendValue(button.dataset.value);
                    });
                });

                document.querySelector('[data-action="clear"]').addEventListener('click', clearDisplay);
                document.querySelector('[data-action="delete"]').addEventListener('click', deleteLast);
                document.querySelector('[data-action="equals"]').addEventListener('click', evaluateExpression);

                display.addEventListener('keydown', (event) => {
                    if (event.key === 'Enter') {
                        evaluateExpression();
                    }
                    if (event.key === 'Escape') {
                        clearDisplay();
                    }
                    if (event.key === 'Backspace') {
                        deleteLast();
                    }
                });

                display.focus();
                updateDisplay();
            </script>
        </body>
        </html>
        """
    )


@app.post("/api/calculate")
async def calculate(payload: CalculationRequest) -> dict[str, Any]:
    try:
        result = _safe_calculate(payload.expression)
        return {"expression": payload.expression, "result": result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("calculator:app", host="0.0.0.0", port=8000, reload=True)
