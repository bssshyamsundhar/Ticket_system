import React from 'react';
import './Card.css';

const Card = ({
    children,
    className = '',
    hover = true,
    glass = true,
    onClick,
    ...props
}) => {
    const cardClass = `
    card
    ${glass ? 'glass-card' : ''}
    ${hover ? 'card-hover' : ''}
    ${className}
  `.trim();

    return (
        <div className={cardClass} onClick={onClick} {...props}>
            {children}
        </div>
    );
};

export default Card;
