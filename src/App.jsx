import { useState } from 'react';


function calculateWinner(squares) {
  const lines = [
    [0, 1, 2],
    [3, 4, 5],
    [6, 7, 8],
    [0, 3, 6],
    [1, 4, 7],
    [2, 5, 8],
    [0, 4, 8],
    [2, 4, 6]
  ];
  for (let i = 0; i < lines.length; i++) {
    const [a, b, c] = lines[i];
    if (squares[a] && squares[a] === squares[b] && squares[a] === squares[c]) {
      return squares[a];
    }
  }
  return null;
}
  function Square({value, onSquareClick}) {
    return <button onClick={onSquareClick} className="square">{value}</button>;
    }
 function Board({xIsNext, squares, onPlay}) {
  function handleClick(index) {
    const nextSquares = squares.slice();
    if (squares[index] || calculateWinner(squares)) return;
    nextSquares[index] = xIsNext ? "X" : "O";
    onPlay(nextSquares);
  }
  const winner = calculateWinner(squares);
  let status; 
  const isFullBoard = !squares.includes(null);
  if (isFullBoard) status = `Stalemate`;
  else if (winner) status = `Winner is: ${winner}`;
  else status = `Next player: ${xIsNext ? 'X': 'O'}`;
  return (
    <>
      <div className='status'>{status}</div>
        {
          [0, 1, 2].map(row => (
            <div key={row} className="board-row">
              {[0, 1, 2].map(col => {
                const index  = row * 3 + col;

                return (
                  <Square onSquareClick={() => handleClick(index)} key={index} value={squares[index]} />
                );
              })}
      </div>
        ))}
    </>
  )
}


export default function Game() {
  const [history, setHistory] = useState([Array(9).fill(null)]);
  const [currentMove, setCurrentMove] = useState(0);
  const currentSquares = history[currentMove];
  const xIsNext = currentMove % 2 === 0;
  function handlePlay(nextSquares) {
    const nextHistory = [...history.slice(0, currentMove + 1), nextSquares];
    setHistory(nextHistory);
    setCurrentMove(nextHistory.length - 1);
  }

  function jumpTo(nextMove) {
    setCurrentMove(nextMove);
  }

  const moves = history.map((squares, move) => {
    let description;
    if (move > 0) {
      description = `Go to move #: ${move}`;
    }
    else {
      description = `Go to game start`;
    }
    return (
      <>
      <li key={move}>
        <button className="move-button" onClick={() => jumpTo(move)}>{description}</button>
      </li>
      </>
    )
  })
  return (
    <>
      <div className='parent-container'>
        <div className='title-container'>
          <div className='title'>Tic Tac Toe</div>
        </div>
        <div className='board'>
          <div className='game-board'>
            <Board xIsNext={xIsNext} squares={currentSquares} onPlay={handlePlay}/>
          </div>
          <div className='game-info'>
            <span className='current-move'>You are at move: [ {currentMove} ]</span>
            <ol className='moves'>{moves}</ol>
          </div>
        </div>
      </div>
    </>
  );
}