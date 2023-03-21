import { useEffect, useState } from "react";
import "./App.css";
import image from "./assets/image.png";
import rectangle from "./assets/rectangle.svg";
import VideoPlayer from "./VideoPlayer";
import axios from "axios";




const App = () => {
  const [startPressed, setStartPressed] = useState(false);
  const [resetPressed, setResetPressed] = useState(false);
  const [stopPressed, setStopPressed] = useState(false);
  const [coordinates, setCoordinates] = useState([0, 0]);

  function handleStartPress() {
    setStartPressed(true);
    // Create function for starting the game 
  }

  function handleResetPress() {
    setResetPressed(true);
  }

  function handleStopPress() {
    setStopPressed(true);
  }

  useEffect(() => {
    axios.get('/api/coordinates')
    .then(response => {
      setCoordinates(response.data);
    }).catch(error => {
      console.error(error);
    });
  }, [coordinates]);

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
        <VideoPlayer />
         
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
