

import React from 'react';

interface Props {
  imageUrl: string;
  circleX: number;
  circleY: number;
}

const ImageWithCircle: React.FC<Props> = ({ imageUrl, circleX, circleY }) => {
  return (
    <div style={{ position: 'relative' }}>
      <img style = {{width: 700, height: 350}}src={imageUrl} alt="Field" />
      <div style={{ position: 'absolute', top: circleY, left: circleX, width: '20px', height: '20px', borderRadius: '50%', backgroundColor: 'white' }}></div>
    </div>
  );
};

export default ImageWithCircle;