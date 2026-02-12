/// 카테고리별 아이콘·색상
import 'package:flutter/material.dart';

const Map<String, CategoryStyle> kCategoryStyles = {
  '식비': CategoryStyle(icon: Icons.restaurant, color: Color(0xFFE57373)),
  '카페': CategoryStyle(icon: Icons.local_cafe, color: Color(0xFFE57373)),
  '교통': CategoryStyle(icon: Icons.directions_transit, color: Color(0xFF64B5F6)),
  '쇼핑': CategoryStyle(icon: Icons.shopping_bag, color: Color(0xFF81C784)),
  '생활': CategoryStyle(icon: Icons.home_work_outlined, color: Color(0xFF81C784)),
  '문화': CategoryStyle(icon: Icons.movie, color: Color(0xFFBA68C8)),
  '여행': CategoryStyle(icon: Icons.travel_explore, color: Color(0xFFBA68C8)),
  '의료': CategoryStyle(icon: Icons.local_hospital, color: Color(0xFF4DD0E1)),
  '교육': CategoryStyle(icon: Icons.school, color: Color(0xFFFFB74D)),
  '통신': CategoryStyle(icon: Icons.phone_android, color: Color(0xFF7986CB)),
  '구독': CategoryStyle(icon: Icons.subscriptions, color: Color(0xFF7986CB)),
  '기타': CategoryStyle(icon: Icons.more_horiz, color: Color(0xFF90A4AE)),
};

CategoryStyle categoryStyle(String category) {
  return kCategoryStyles[category] ?? kCategoryStyles['기타']!;
}

class CategoryStyle {
  const CategoryStyle({required this.icon, required this.color});
  final IconData icon;
  final Color color;
}
