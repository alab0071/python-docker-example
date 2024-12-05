from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os

app = FastAPI()

# Define the Tic-Tac-Toe game
class TicTacToe:
    def __init__(self):
        self.board = [" " for _ in range(9)]  # A fresh 3x3 board!
        self.current_winner = None  # Tracks the winner (if any).

    def make_move(self, index: int, symbol: str):
        if 0 <= index < 9 and self.board[index] == " ":
            self.board[index] = symbol
            if self.check_winner(symbol):
                self.current_winner = symbol
            return True
        return False

    def check_winner(self, symbol: str):
        win_conditions = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
            [0, 4, 8], [2, 4, 6]              # Diagonals
        ]
        return any(all(self.board[i] == symbol for i in condition) for condition in win_conditions)

    def current_state(self):
        return self.board

game = TicTacToe()

# Pydantic model for making moves
class Move(BaseModel):
    index: int
    symbol: str

@app.get("/")
def read_root():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Interactive Tic-Tac-Toe</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; }
            .board { display: grid; grid-template-columns: repeat(3, 100px); gap: 5px; margin: 20px auto; }
            .cell { width: 100px; height: 100px; border: 1px solid black; font-size: 24px; display: flex; justify-content: center; align-items: center; cursor: pointer; }
            .cell.taken { cursor: not-allowed; color: gray; }
        </style>
    </head>
    <body>
        <h1>Tic-Tac-Toe</h1>
        <div id="message"></div>
        <div class="board" id="board"></div>
        <button onclick="resetGame()">Reset Game</button>
        <script>
            const baseURL = "http://localhost:8000";

            // Initialize board
            async function loadBoard() {
                const response = await fetch(`${baseURL}/board`);
                const data = await response.json();
                const board = document.getElementById("board");
                board.innerHTML = "";
                data.board.forEach((cell, index) => {
                    const cellDiv = document.createElement("div");
                    cellDiv.className = "cell";
                    cellDiv.textContent = cell;
                    if (cell !== " ") cellDiv.classList.add("taken");
                    cellDiv.onclick = () => makeMove(index);
                    board.appendChild(cellDiv);
                });
            }

            // Make a move
            async function makeMove(index) {
                const symbol = prompt("Enter your symbol (X or O):");
                if (!symbol || !["X", "O"].includes(symbol.toUpperCase())) {
                    alert("Invalid symbol! Enter X or O.");
                    return;
                }
                try {
                    const response = await fetch(`${baseURL}/move`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ index, symbol }),
                    });
                    const result = await response.json();
                    if (response.ok) {
                        document.getElementById("message").innerText = result.message;
                        loadBoard();
                    } else {
                        alert(result.detail);
                    }
                } catch (error) {
                    console.error("Error making move:", error);
                }
            }

            // Reset the game
            async function resetGame() {
                try {
                    await fetch(`${baseURL}/reset`, { method: "POST" });
                    document.getElementById("message").innerText = "Game reset!";
                    loadBoard();
                } catch (error) {
                    console.error("Error resetting game:", error);
                }
            }

            // Load the initial board
            loadBoard();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/board")
def get_board():
    return {"board": game.current_state()}

@app.post("/move")
def make_move(move: Move):
    if game.current_winner:
        raise HTTPException(status_code=400, detail="Game already has a winner!")
    if game.make_move(move.index, move.symbol):
        if game.current_winner:
            return {"message": f"Player {move.symbol} wins!", "board": game.current_state()}
        return {"message": "Move successful!", "board": game.current_state()}
    else:
        raise HTTPException(status_code=400, detail="Invalid move. Try again.")

@app.post("/reset")
def reset_game():
    global game
    game = TicTacToe()
    return {"message": "Game has been reset!"}

