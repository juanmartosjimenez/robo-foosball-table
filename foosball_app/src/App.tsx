import {useEffect, useState } from "react";
import React from "react";
import "./App.css";
import image from "./assets/image.png";
import axios from "axios";
import WhiteCircle from "./WhiteCircle";
import Button from "react-bootstrap/Button";
import "bootstrap/dist/css/bootstrap.min.css";
import {Card} from "react-bootstrap";



interface Coordinates {
  x: number;
  y: number;
}
const App = () => {
  const [startPressed, setStartPressed] = useState(false);
  const [powerOn, setPowerOn] = useState(false);
  const [resetPressed, setResetPressed] = useState(false);
  const [coordinates, setCoordinates] = useState<Coordinates>({x: 0, y: 0});
  const [statusMessage, setStatusMessage] = useState('');

  const [circleX, setCircleX] = useState(0);
  const [circleY, setCircleY] = useState(0);

  const handlePowerOn = async() => {
    setPowerOn(true);
    try {
      const response = await axios.post('http://127.0.0.1:5000/api/power_on', {
        hardware_type: 'printer',
        action: 'start',
      });
      setStatusMessage('Hardware started successfully');
    } catch (error) {
      setStatusMessage('Failed to start hardware');
    }
  };

  const handleStartPress = async() => {
    if(powerOn) {
      setStartPressed(true);
    
      try {
        const response = await axios.post('http://127.0.0.1:5000/api/start', {
          hardware_type: 'printer',
          action: 'start',
        });
        setStatusMessage('Hardware started successfully');
      } catch (error) {
        setStatusMessage('Failed to start hardware');
      }
    }
  };
    // Create function for starting the game 

  const handleResetPress = async() => {
    if(powerOn) {
      setResetPressed(true);
      setStartPressed(false);
      setPowerOn(false);
    
      try {
        const response = await axios.post('http://127.0.0.1:5000/api/reset', {
          hardware_type: 'printer',
          action: 'start',
        });
        setStatusMessage('Hardware started successfully');
      } catch (error) {
        setStatusMessage('Failed to start hardware');
      }
    }
  };

  const handleCircleMove = () => {
    axios.get('http://127.0.0.1:5000/api/coordinates')
      .then(response => setCoordinates(response.data))
      .catch(error => console.error(error));
    setCircleX(coordinates.x);
    setCircleY(coordinates.y);
  };

  
  useEffect(() => {
    const intervalId = setInterval(() => {
      axios.get('http://127.0.0.1:5000/api/coordinates')
      .then(response => setCircleX(response.data.x))
      .catch(error => console.error(error));
    setCircleX(coordinates.x);
    setCircleY(coordinates.y);
    console.log(coordinates);
    console.log(circleX);
    console.log(circleY);
    }, 1000);

    return () => {
      clearInterval(intervalId);
    }
  }, []);
  

  return (
    <div >
      <div className="rectangle-1">
        <div className = "right">
            <img className="image-1" src={image} alt="northeastern logo"/>
        </div>

        <Card style = {{color: 'gray'}}>
          <Card.Body style={{ fontSize: '50px' }}
                      className= "text-center">
            <Card.Title>RIFT</Card.Title>
            <Card.Subtitle>Robotic Intelligence Foosball Table</Card.Subtitle>
          </Card.Body>
        </Card>
      
        <div className="flex-container-1">
          <Button 
            size="lg"
            style= {{fontSize: '20px'}}
            className={powerOn ? 'dimmed' : 'not-pressed'}
            onClick={handlePowerOn}
          >
            Power On 
          </Button>

          <Button
            size="lg"
            style= {{fontSize: '20px'}}
            className={startPressed ? 'dimmed' : 'not-pressed'}
            onClick={handleStartPress}
          >
            Start Game
          </Button>
          
          <Button 
            size="lg"
            style= {{fontSize: '20px'}}
            className={resetPressed ? 'dimmed' : 'not-pressed'}
            onClick={handleResetPress}
          >
            Shut Down 
          </Button>
        </div>
        
        <Card style = {{color: 'gray', marginBottom: '5px'}}>
          <Card.Body style={{ fontSize: '24px' }}>
            <Card.Title>Current Game State</Card.Title>
          </Card.Body>
        </Card>
        <div>
          <WhiteCircle imageUrl="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQxMLxE4TIhrIVc-5M3Jiv7Z6R2ho8VtlZ_c0U4Q8BJ&s" circleX={circleX} circleY={circleY}/>
        </div>
         
        <Card style = {{color: 'gray', marginTop: '5px'}}>
          <Card.Body style={{ fontSize: '24px' }}>
            <Card.Title>Coordinates of Ball: [ {coordinates.x} , {coordinates.y} ]</Card.Title>
          </Card.Body>
        </Card>
            
      </div>
    </div>
  );
};
export default App;
