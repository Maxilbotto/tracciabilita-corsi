-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: May 22, 2025 at 12:26 PM
-- Server version: 8.0.30
-- PHP Version: 8.1.10

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `tracciabilita_corsi`
--

-- --------------------------------------------------------

--
-- Table structure for table `corsi_formazione`
--

CREATE TABLE `corsi_formazione` (
  `id_corso` int NOT NULL,
  `titolo` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `numero_ore` int NOT NULL,
  `ente_erogatore` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `descrizione` text COLLATE utf8mb4_unicode_ci,
  `tipologia` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `data_inizio` date DEFAULT NULL,
  `data_fine` date DEFAULT NULL,
  `costo` decimal(10,2) DEFAULT NULL,
  `durata_minuti` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `corsi_formazione`
--

INSERT INTO `corsi_formazione` (`id_corso`, `titolo`, `numero_ore`, `ente_erogatore`, `descrizione`, `tipologia`, `data_inizio`, `data_fine`, `costo`, `durata_minuti`) VALUES
(1, 'Corso Base Sicurezza', 8, 'Formazione S.r.l.', 'Corso introduttivo sulla sicurezza nei luoghi di lavoro.', 'Obbligatorio', '2025-06-01', '2025-06-01', '120.00', 480);

-- --------------------------------------------------------

--
-- Table structure for table `dipendenti`
--

CREATE TABLE `dipendenti` (
  `id_dipendente` int NOT NULL,
  `nome` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `cognome` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `dipendenti`
--

INSERT INTO `dipendenti` (`id_dipendente`, `nome`, `cognome`) VALUES
(1, 'Mario', 'Rossi');

-- --------------------------------------------------------

--
-- Table structure for table `partecipazioni`
--

CREATE TABLE `partecipazioni` (
  `id_partecipazione` int NOT NULL,
  `id_dipendente` int NOT NULL,
  `id_corso` int NOT NULL,
  `data_completamento` date NOT NULL,
  `certificato_allegato` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `data_scadenza_certificazione` date DEFAULT NULL,
  `costo_sostenuto` decimal(10,2) DEFAULT NULL,
  `note` text COLLATE utf8mb4_unicode_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `partecipazioni`
--

INSERT INTO `partecipazioni` (`id_partecipazione`, `id_dipendente`, `id_corso`, `data_completamento`, `certificato_allegato`, `data_scadenza_certificazione`, `costo_sostenuto`, `note`) VALUES
(1, 1, 1, '2025-05-01', 'certificato_mario_rossi.pdf', '2027-05-01', '120.00', 'Partecipazione completata con successo');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `corsi_formazione`
--
ALTER TABLE `corsi_formazione`
  ADD PRIMARY KEY (`id_corso`);
ALTER TABLE `corsi_formazione` ADD FULLTEXT KEY `titolo` (`titolo`);

--
-- Indexes for table `dipendenti`
--
ALTER TABLE `dipendenti`
  ADD PRIMARY KEY (`id_dipendente`);
ALTER TABLE `dipendenti` ADD FULLTEXT KEY `nome` (`nome`,`cognome`);
ALTER TABLE `dipendenti` ADD FULLTEXT KEY `nome_2` (`nome`,`cognome`);

--
-- Indexes for table `partecipazioni`
--
ALTER TABLE `partecipazioni`
  ADD PRIMARY KEY (`id_partecipazione`),
  ADD KEY `id_dipendente` (`id_dipendente`),
  ADD KEY `id_corso` (`id_corso`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `corsi_formazione`
--
ALTER TABLE `corsi_formazione`
  MODIFY `id_corso` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `dipendenti`
--
ALTER TABLE `dipendenti`
  MODIFY `id_dipendente` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `partecipazioni`
--
ALTER TABLE `partecipazioni`
  MODIFY `id_partecipazione` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `partecipazioni`
--
ALTER TABLE `partecipazioni`
  ADD CONSTRAINT `partecipazioni_ibfk_1` FOREIGN KEY (`id_dipendente`) REFERENCES `dipendenti` (`id_dipendente`),
  ADD CONSTRAINT `partecipazioni_ibfk_2` FOREIGN KEY (`id_corso`) REFERENCES `corsi_formazione` (`id_corso`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
