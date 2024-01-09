/*
 Navicat Premium Data Transfer

 Source Server         : ke beta project
 Source Server Type    : MariaDB
 Source Server Version : 100612
 Source Host           : localhost:3306
 Source Schema         : test

 Target Server Type    : MariaDB
 Target Server Version : 100612
 File Encoding         : 65001

 Date: 09/01/2024 08:27:39
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for child_table
-- ----------------------------
DROP TABLE IF EXISTS `child_table`;
CREATE TABLE `child_table`  (
  `id` int(11) NOT NULL,
  `parent_id` int(11) NOT NULL,
  `desc` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`, `parent_id`) USING BTREE,
  INDEX `parent_id`(`parent_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of child_table
-- ----------------------------
INSERT INTO `child_table` VALUES (1, 1, 'child row 1');
INSERT INTO `child_table` VALUES (2, 1, 'child row 2');
INSERT INTO `child_table` VALUES (3, 2, 'child row 21');
INSERT INTO `child_table` VALUES (4, 2, 'child row 22');
INSERT INTO `child_table` VALUES (5, 2, 'child row 23');

-- ----------------------------
-- Table structure for grandchild_table
-- ----------------------------
DROP TABLE IF EXISTS `grandchild_table`;
CREATE TABLE `grandchild_table`  (
  `id` int(11) NOT NULL,
  `child_id` int(11) NOT NULL,
  `desc` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`, `child_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of grandchild_table
-- ----------------------------
INSERT INTO `grandchild_table` VALUES (1, 1, 'children row 1');
INSERT INTO `grandchild_table` VALUES (2, 1, 'children row 2');
INSERT INTO `grandchild_table` VALUES (3, 2, 'children row 21');
INSERT INTO `grandchild_table` VALUES (4, 2, 'children row 22');
INSERT INTO `grandchild_table` VALUES (5, 3, 'children row 31');

-- ----------------------------
-- Table structure for parent_table
-- ----------------------------
DROP TABLE IF EXISTS `parent_table`;
CREATE TABLE `parent_table`  (
  `id` int(11) NOT NULL,
  `desc` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of parent_table
-- ----------------------------
INSERT INTO `parent_table` VALUES (1, 'parent row 1');
INSERT INTO `parent_table` VALUES (2, 'parent row 2');

-- ----------------------------
-- Table structure for person
-- ----------------------------
DROP TABLE IF EXISTS `person`;
CREATE TABLE `person`  (
  `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT,
  `id_team` int(10) UNSIGNED NOT NULL,
  `person_name` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `notes` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `team_person`(`id`, `id_team`) USING BTREE,
  INDEX `id_team`(`id_team`) USING BTREE,
  CONSTRAINT `person_ibfk_1` FOREIGN KEY (`id_team`) REFERENCES `team` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of person
-- ----------------------------
INSERT INTO `person` VALUES (1, 1, 'child 1', 'team 1 member ke 1');
INSERT INTO `person` VALUES (2, 1, 'child 2', 'team 1 member ke 2');
INSERT INTO `person` VALUES (3, 3, 'child1', 'team 3 member ke 1');

-- ----------------------------
-- Table structure for team
-- ----------------------------
DROP TABLE IF EXISTS `team`;
CREATE TABLE `team`  (
  `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT,
  `team_name` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `team_name`(`team_name`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 5 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of team
-- ----------------------------
INSERT INTO `team` VALUES (1, 'team1', 'parent 1');
INSERT INTO `team` VALUES (2, 'team2', 'parent 1');
INSERT INTO `team` VALUES (3, 'team3', 'parent 1');

SET FOREIGN_KEY_CHECKS = 1;
