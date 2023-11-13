-- Table: Station Information
create table ir_train_station_trst(
	trst_station_code varchar(10),
	trst_station_name varchar(100),
	trst_state_name varchar(100),
	trst_railway_zone varchar(100),
	trst_railway_division varchar(100),
	constraint trst_pk primary key (trst_station_code)
);
select * from ir_train_station_trst;

-- Table: Train Information
create table ir_train_information_trin(
	trin_train_number varchar(10),
	trin_train_name varchar(500) not null,
	trin_source_station varchar(100) not null,
	trin_destination_station varchar(100) not null,
	trin_train_type varchar(100),
	trin_service_days varchar(200),
	trin_train_coach_class varchar(200),
	trin_travel_duration varchar(200),
	trin_travel_distance int,
	trin_number_of_stops int,
	trin_average_speed int,
	constraint trin_pk primary key (trin_train_number),
	constraint trin_src_fk foreign key (trin_source_station) references ir_train_station_trst(trst_station_code),
	constraint trin_dest_fk foreign key (trin_destination_station) references ir_train_station_trst(trst_station_code)
);
select * from ir_train_information_trin;

-- Table: Route Information
create table ir_train_route_trro(
	trro_train_schedule_id int not null auto_increment,
	trro_train_number varchar(10),
	trro_route_station varchar(10),
	trro_arrival_time varchar(100),
	trro_departure_time varchar(100),
	trro_halt_duration int,
	trro_distance_travelled int,
	trro_halt_number int,
	constraint trro_pk primary key (trro_train_schedule_id),
	constraint trro_train_fk foreign key (trro_train_number) references ir_train_information_trin(trin_train_number),
	constraint trro_station_fk foreign key (trro_route_station) references ir_train_station_trst(trst_station_code)
);

select * from ir_train_route_trro;