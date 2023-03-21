import React, { useRef } from 'react';

function VideoPlayer() {
  const videoRef = useRef<HTMLVideoElement>(null);

  function handlePlay() {
    videoRef.current?.play();
  }

  function handlePause() {
    videoRef.current?.pause();
  }

  return (
    <div>
      <video ref={videoRef} width={640} height={360}>
        <source src="video.mp4" type="video/mp4" />
        Your browser does not support the video tag.
      </video>
      <div className = "button-container">
        <button className = "button"
        style = {{fontSize: 25}}
        onClick={handlePlay}>
          Play
          </button>
        <button className = "button"
        style = {{fontSize: 25}}
        onClick={handlePause}>
          Pause
          </button>
      </div>
    </div>
  );
}

export default VideoPlayer;