# Sudoku

## Description

Sudoku is a logic-based number placement puzzle. The objective is to fill a 9x9 grid with digits so that each column, each row, and each of the nine 3x3 subgrids that compose the grid contain all of the digits from 1 to 9.

## How to Run

1. Ensure you have Python installed on your machine.
2. Install the required libraries:
   ```bash
   pip install pygame
   ```
3. Start the server by running:
   ```bash
   python server-sudoku.py
   ```
4. In a separate terminal, start the client by running:
   ```bash
   python client-sudoku.py
   ```

## How to Play

- Once the game starts, two players can connect to the server.
- Players take turns to select a cell and input a number from 1 to 9.
- The game continues until all empty cells have been filled.
- The scores are displayed on the side panel, and the winner is announced at the end of the game.
