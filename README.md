# Solar Data Platform

A comprehensive platform for collecting, storing, and analyzing solar inverter data.

## Features

- Real-time data collection from GoodWe SEMS inverters
- Time-series data storage using InfluxDB
- RESTful API for data access and management
- Dynamic inverter management with containerization
- Modern React frontend for data visualization

## Architecture

The platform consists of several components:

- **Backend**: FastAPI-based REST API
- **Frontend**: React-based web interface
- **Database**: PostgreSQL for metadata storage
- **Time-series DB**: InfluxDB for metrics storage
- **Inverter Scrapers**: Containerized Python scripts for data collection

## Prerequisites

- Docker and Docker Compose
- Python 3.9+
- Node.js 16+

## Quick Start

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd solar-platform
   ```

2. Create environment files:
   ```bash
   cp .env.example .env
   ```

3. Start the services:
   ```bash
   docker-compose up -d
   ```

4. Access the services:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - InfluxDB: http://localhost:8086
   - PostgreSQL: localhost:5432

## API Endpoints

### Inverter Management
- `GET /inverters` - List all inverters
- `POST /inverters` - Add new inverter
- `GET /inverters/{id}` - Get inverter details
- `PUT /inverters/{id}` - Update inverter
- `DELETE /inverters/{id}` - Remove inverter

### Data Collection
- `GET /inverter-status/{inverter_sn}` - Get inverter status
- `GET /power-generation/{property_id}` - Get power generation data
- `GET /my-home/{property_id}` - Get home metrics
- `GET /device-metrics/{device_id}` - Get device-specific metrics

### Configuration
- `GET /config/influx` - Get InfluxDB configuration

## Data Points Collected

### Inverter Status
- Current Power Output
- Daily Energy Generation
- Monthly Energy Generation
- Total Energy Generation
- Total Operating Hours
- Online/Offline Status

### Home Metrics
- Power Production
- Home Consumption
- Battery Charging
- Grid Export
- Climate Conditions
- Rain Percentage

## Development

1. Set up development environment:
   ```bash
   # Backend
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

   # Frontend
   cd frontend
   npm install
   ```

2. Run development servers:
   ```bash
   # Backend
   uvicorn main:app --reload

   # Frontend
   npm start
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.