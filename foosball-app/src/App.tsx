import { useEffect, useState } from "react";
import React from "react";
import "./App.css";
import "./tailwind.css";
import image from "./assets/image.png";
import axios from "axios";
import WhiteCircle from "./WhiteCircle";




const App = () => {
  const [startPressed, setStartPressed] = useState(false);
  const [resetPressed, setResetPressed] = useState(false);
  const [stopPressed, setStopPressed] = useState(false);
  const [coordinates, setCoordinates] = useState([0, 0]);

  const [circleX, setCircleX] = useState(0);
  const [circleY, setCircleY] = useState(0);

  const handleStartPress = async() => {
    setStartPressed(true);
    const response = await fetch('/start');
    const data = await response.json();
    console.log(data);
    // Create function for starting the game 
  }

  const handleResetPress = async() => {
    setResetPressed(true);
    const response = await fetch('/reset');
    const data = await response.json();
    console.log(data);
  }

  const handleStopPress = async() => {
    setStopPressed(true);
    const response = await fetch('/stop');
    const data = await response.json();
    console.log(data);
  }

  const handleMouseMove = (event: React.MouseEvent<HTMLImageElement, MouseEvent>) => {
    const imageRect = event.currentTarget.getBoundingClientRect();
    const imageWidth = 680;
    const imageHeight = 330;
    const x = event.clientX - imageRect.left - 10;
    const y = event.clientY - imageRect.top - 10;

    const adjusted_x = imageWidth - x;
    const adjusted_y = imageHeight - y;

    setCircleX(x);
    setCircleY(y);
    setCoordinates([adjusted_x, adjusted_y]);
  };

  /*
  useEffect(() => {
    axios.get('/coordinates')
    .then(response => {
      setCoordinates(response.data);
    }).catch(error => {
      console.error(error);
    });
  }, [coordinates]);
  */

  return (
    <div className="robo-foosball-ui">
      <div className="rectangle-1">
        <div className = "right">
            <img className="image-1" src={image} alt="northeastern logo"/>
        </div>

        <div className="video-text-box">
            Robotic Foosball Table
        </div>


        <div className="flex-container-1">
          <button 
            className={startPressed ? 'dimmed' : 'not-pressed'}
            onClick={handleStartPress}
          >
            Start Game
          </button>
          <button 
            className={resetPressed ? 'dimmed' : 'not-pressed'}
            onClick={handleResetPress}
          >
            Reset Game 
          </button>
          <button 
            className={stopPressed ? 'dimmed' : 'not-pressed'}
            onClick={handleStopPress}
          >
            Emerg. Stop
          </button>
        </div>
        
        <div className="video-text-box">
          Video Feed of Foosball Table
        </div>
        <div onMouseMove={handleMouseMove}>
          <WhiteCircle imageUrl="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQxMLxE4TIhrIVc-5M3Jiv7Z6R2ho8VtlZ_c0U4Q8BJ&s" circleX={circleX} circleY={circleY}/>
        </div>
         
        <div className="video-text-box">
          <span className="xy">
            Coordinates of Ball: [ {coordinates[0]} , {coordinates[1]} ]
          </span>
        </div>
      </div>
    </div>
  );
};
export default App;
