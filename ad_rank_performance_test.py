#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AD_RANK 광고 엔진 성능 테스트 스크립트

이 스크립트는 AD_RANK 요구사항에 따라 광고 상품의 랭킹을 계산합니다.

주요 기능:
1. 카테고리별 AD_RANK 계산 (입찰가 × 클릭전환율)
2. CPC 계산 (다음 순위 AD_RANK ÷ 본인 클릭전환율 + 1)
3. 가산점 시스템 (노출 1000회 + 구매 1회)
4. 노출 비중 계산 (30% 상한 제한)
5. 성능 측정

AD_RANK 요구사항 문서: docs/1. 정리/1-3 AD_RANK_요구사항.md

Author: AD_RANK Development Team
Version: 1.0.0
Last Updated: 2024-01-15
"""

import datetime
import time
import random
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import logging

# =============================================================================
# 상수 정의
# =============================================================================

class AdRankConstants:
    """AD_RANK 계산 관련 상수들"""
    
    # 노출 기준치 (회)
    EXPOSURE_THRESHOLD = 1000
    
    # 구매 기준치 (회)
    PURCHASE_THRESHOLD = 1
    
    # 노출 비중 상한선 (%)
    MAX_EXPOSURE_RATIO = 30.0
    
    # 클릭전환율 최소값 (CTR이 0인 경우)
    MIN_CTR = 0.1
    
    # CPC 계산 시 추가 금액 (원)
    CPC_ADDITION = 1
    
    # 소수점 자릿수
    DECIMAL_PLACES = 2
    
    # 성능 기준 (ms)
    PERFORMANCE_EXCELLENT = 1.0  # 1ms 이하: 우수
    PERFORMANCE_GOOD = 3.0       # 3ms 이하: 양호
    PERFORMANCE_ACCEPTABLE = 10.0 # 10ms 이하: 허용
    PERFORMANCE_POOR = 1000.0    # 1초 이상: 불량

# =============================================================================
# 데이터 모델 정의
# =============================================================================

@dataclass
class ProductData:
    """상품 기본 데이터 모델"""
    상품명: str
    입찰가: int
    클릭전환율: float
    노출수: int
    구매수: int

@dataclass
class AdRankResult:
    """AD_RANK 계산 결과 모델"""
    상품명: str
    입찰가: int
    클릭전환율: float
    노출수: int
    구매수: int
    AD_RANK: float
    노출_가산점: int
    구매_가산점: int
    최종_점수: float
    CPC: int
    노출_비중: float

@dataclass
class PerformanceMetrics:
    """성능 측정 결과 모델"""
    처리_시간_ms: float
    총_상품_수: int
    카테고리_수: int
    평균_카테고리_처리시간_ms: float
    상품당_평균_처리시간_ms: float

# =============================================================================
# 로깅 설정
# =============================================================================

def setup_logging() -> None:
    """로깅 설정 초기화"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            
        ]
    )

# =============================================================================
# 샘플 데이터 생성
# =============================================================================

def generate_sample_data() -> Dict[str, List[ProductData]]:
    """
    AD_RANK 요구사항에 맞는 샘플 데이터 생성
    
    Returns:
        Dict[str, List[ProductData]]: 카테고리별 상품 데이터
        
    데이터 구조:
    - 입찰가: 최대 입찰가 (원)
    - 클릭전환율: 클릭 대비 전환율 (%)
    - 노출수: 누적 노출 수
    - 구매수: 노출 1000회 동안 구매 수
    
    예시:
        {
            "노트북": [
                ProductData("삼성 갤럭시북", 2000, 5.1, 1200, 2),
                ProductData("LG 그램", 1800, 4.8, 1100, 1),
                ...
            ],
            "스마트폰": [...],
            "태블릿": [...]
        }
    """
    
    # 노트북 카테고리 데이터 생성 (100개)
    notebook_products = [
        # 삼성 노트북 (20개)
        ProductData("삼성 갤럭시북2", 2200, 5.2, 1300, 3),
        ProductData("삼성 갤럭시북3", 2400, 5.3, 1400, 3),
        ProductData("삼성 갤럭시북4", 2600, 5.4, 1500, 4),
        ProductData("삼성 갤럭시북5", 2800, 5.5, 1600, 4),
        ProductData("삼성 갤럭시북6", 3000, 5.6, 1700, 5),
        ProductData("삼성 갤럭시북7", 3200, 5.7, 1800, 5),
        ProductData("삼성 갤럭시북8", 3400, 5.8, 1900, 6),
        ProductData("삼성 갤럭시북9", 3600, 5.9, 2000, 6),
        ProductData("삼성 갤럭시북10", 3800, 6.0, 2100, 7),
        ProductData("삼성 갤럭시북11", 4000, 6.1, 2200, 7),
        ProductData("삼성 갤럭시북12", 4200, 6.2, 2300, 8),
        ProductData("삼성 갤럭시북13", 4400, 6.3, 2400, 8),
        ProductData("삼성 갤럭시북14", 4600, 6.4, 2500, 9),
        ProductData("삼성 갤럭시북15", 4800, 6.5, 2600, 9),
        ProductData("삼성 갤럭시북16", 5000, 6.6, 2700, 10),
        ProductData("삼성 갤럭시북17", 5200, 6.7, 2800, 10),
        ProductData("삼성 갤럭시북18", 5400, 6.8, 2900, 11),
        ProductData("삼성 갤럭시북19", 5600, 6.9, 3000, 11),
        ProductData("삼성 갤럭시북20", 5800, 7.0, 3100, 12),
        ProductData("삼성 갤럭시북21", 60000, 7.1, 3200, 12),
        
        # LG 노트북 (15개)
        ProductData("LG 그램2", 1900, 4.9, 1150, 2),
        ProductData("LG 그램3", 2000, 5.0, 1200, 2),
        ProductData("LG 그램4", 2100, 5.1, 1250, 3),
        ProductData("LG 그램5", 2200, 5.2, 1300, 3),
        ProductData("LG 그램6", 2300, 5.3, 1350, 4),
        ProductData("LG 그램7", 2400, 5.4, 1400, 4),
        ProductData("LG 그램8", 2500, 5.5, 1450, 5),
        ProductData("LG 그램9", 2600, 5.6, 1500, 5),
        ProductData("LG 그램10", 2700, 5.7, 1550, 6),
        ProductData("LG 그램11", 2800, 5.8, 1600, 6),
        ProductData("LG 그램12", 2900, 5.9, 1650, 7),
        ProductData("LG 그램13", 3000, 6.0, 1700, 7),
        ProductData("LG 그램14", 3100, 6.1, 1750, 8),
        ProductData("LG 그램15", 3200, 6.2, 1800, 8),
        ProductData("LG 그램16", 3300, 6.3, 1850, 9),
        
        # 애플 노트북 (15개)
        ProductData("애플 맥북프로2", 2700, 6.3, 1600, 4),
        ProductData("애플 맥북프로3", 2900, 6.4, 1700, 4),
        ProductData("애플 맥북프로4", 3100, 6.5, 1800, 5),
        ProductData("애플 맥북프로5", 3300, 6.6, 1900, 5),
        ProductData("애플 맥북프로6", 3500, 6.7, 2000, 6),
        ProductData("애플 맥북프로7", 3700, 6.8, 2100, 6),
        ProductData("애플 맥북프로8", 3900, 6.9, 2200, 7),
        ProductData("애플 맥북프로9", 4100, 7.0, 2300, 7),
        ProductData("애플 맥북프로10", 4300, 7.1, 2400, 8),
        ProductData("애플 맥북프로11", 4500, 7.2, 2500, 8),
        ProductData("애플 맥북프로12", 4700, 7.3, 2600, 9),
        ProductData("애플 맥북프로13", 4900, 7.4, 2700, 9),
        ProductData("애플 맥북프로14", 5100, 7.5, 2800, 10),
        ProductData("애플 맥북프로15", 5300, 7.6, 2900, 10),
        ProductData("애플 맥북프로16", 5500, 7.7, 3000, 11),
        
        # HP 노트북 (10개)
        ProductData("HP 엘리트북2", 1700, 4.3, 950, 2),
        ProductData("HP 엘리트북3", 1800, 4.4, 1000, 2),
        ProductData("HP 엘리트북4", 1900, 4.5, 1050, 3),
        ProductData("HP 엘리트북5", 2000, 4.6, 1100, 3),
        ProductData("HP 엘리트북6", 2100, 4.7, 1150, 4),
        ProductData("HP 엘리트북7", 2200, 4.8, 1200, 4),
        ProductData("HP 엘리트북8", 2300, 4.9, 1250, 5),
        ProductData("HP 엘리트북9", 2400, 5.0, 1300, 5),
        ProductData("HP 엘리트북10", 2500, 5.1, 1350, 6),
        ProductData("HP 엘리트북11", 2600, 5.2, 1400, 6),
        
        # 델 노트북 (10개)
        ProductData("델 XPS2", 2400, 5.6, 1400, 3),
        ProductData("델 XPS3", 2600, 5.7, 1500, 3),
        ProductData("델 XPS4", 2800, 5.8, 1600, 4),
        ProductData("델 XPS5", 3000, 5.9, 1700, 4),
        ProductData("델 XPS6", 3200, 6.0, 1800, 5),
        ProductData("델 XPS7", 3400, 6.1, 1900, 5),
        ProductData("델 XPS8", 3600, 6.2, 2000, 6),
        ProductData("델 XPS9", 3800, 6.3, 2100, 6),
        ProductData("델 XPS10", 4000, 6.4, 2200, 7),
        ProductData("델 XPS11", 4200, 6.5, 2300, 7),
        
        # 레노버 노트북 (10개)
        ProductData("레노버 씽크패드2", 1800, 4.6, 1050, 2),
        ProductData("레노버 씽크패드3", 1900, 4.7, 1100, 2),
        ProductData("레노버 씽크패드4", 2000, 4.8, 1150, 3),
        ProductData("레노버 씽크패드5", 2100, 4.9, 1200, 3),
        ProductData("레노버 씽크패드6", 2200, 5.0, 1250, 4),
        ProductData("레노버 씽크패드7", 2300, 5.1, 1300, 4),
        ProductData("레노버 씽크패드8", 2400, 5.2, 1350, 5),
        ProductData("레노버 씽크패드9", 2500, 5.3, 1400, 5),
        ProductData("레노버 씽크패드10", 2600, 5.4, 1450, 6),
        ProductData("레노버 씽크패드11", 2700, 5.5, 1500, 6),
        
        # ASUS 노트북 (10개)
        ProductData("ASUS 젠북2", 2000, 5.0, 1100, 2),
        ProductData("ASUS 젠북3", 2100, 5.1, 1150, 2),
        ProductData("ASUS 젠북4", 2200, 5.2, 1200, 3),
        ProductData("ASUS 젠북5", 2300, 5.3, 1250, 3),
        ProductData("ASUS 젠북6", 2400, 5.4, 1300, 4),
        ProductData("ASUS 젠북7", 2500, 5.5, 1350, 4),
        ProductData("ASUS 젠북8", 2600, 5.6, 1400, 5),
        ProductData("ASUS 젠북9", 2700, 5.7, 1450, 5),
        ProductData("ASUS 젠북10", 2800, 5.8, 1500, 6),
        ProductData("ASUS 젠북11", 2900, 5.9, 1550, 6),
        
        # MSI 노트북 (10개)
        ProductData("MSI 프레스티지2", 2200, 5.4, 1300, 3),
        ProductData("MSI 프레스티지3", 2300, 5.5, 1350, 3),
        ProductData("MSI 프레스티지4", 2400, 5.6, 1400, 4),
        ProductData("MSI 프레스티지5", 2500, 5.7, 1450, 4),
        ProductData("MSI 프레스티지6", 2600, 5.8, 1500, 5),
        ProductData("MSI 프레스티지7", 2700, 5.9, 1550, 5),
        ProductData("MSI 프레스티지8", 2800, 6.0, 1600, 6),
        ProductData("MSI 프레스티지9", 2900, 6.1, 1650, 6),
        ProductData("MSI 프레스티지10", 3000, 6.2, 1700, 7),
        ProductData("MSI 프레스티지11", 3100, 6.3, 1750, 7),
    ]

    # 스마트폰 카테고리 데이터 (18개)
    smartphone_products = [
        ProductData("삼성 갤럭시S24", 1800, 5.8, 10600, 4),
        ProductData("삼성 갤럭시S25", 3000, 5.8, 7400, 2),
        ProductData("삼성 갤럭시S26", 3100, 5.8, 1600, 4),
        ProductData("삼성 갤럭시S27", 3200, 5.8, 1600, 4),
        ProductData("삼성 갤럭시S28", 3300, 5.8, 1600, 4),
        ProductData("삼성 갤럭시S29", 3400, 5.8, 1600, 4),
        ProductData("삼성 갤럭시S30", 3500, 5.8, 1600, 4),
        ProductData("삼성 갤럭시S31", 3600, 5.8, 1600, 4),
        ProductData("삼성 갤럭시S32", 3700, 5.8, 1600, 4),
        ProductData("삼성 갤럭시S33", 3800, 5.8, 1600, 4),
        ProductData("애플 아이폰15", 2200, 6.5, 1800, 5),
        ProductData("LG 벨벳", 1200, 4.2, 900, 1),
        ProductData("구글 픽셀8", 1600, 5.1, 1200, 2),
        ProductData("샤오미 13T", 1000, 4.8, 1100, 2),
        ProductData("원플러스 12", 1400, 4.6, 1000, 1),
        ProductData("화웨이 P60", 1300, 4.4, 950, 1),
        ProductData("OPPO 리노10", 900, 3.9, 800, 0),
        ProductData("비보 V29", 800, 3.6, 750, 0),
        ProductData("소니 엑스페리아", 1500, 4.7, 1050, 1),
    ]
    
    # 태블릿 카테고리 데이터(10개)
    tablet_products = [
        ProductData("애플 아이패드프로", 2000, 6.0, 1400, 3),
        ProductData("삼성 갤럭시탭S9", 1700, 5.2, 1200, 2),
        ProductData("애플 아이패드에어", 1500, 5.5, 1300, 2),
        ProductData("마이크로소프트 서피스", 1800, 4.8, 1100, 1),
        ProductData("삼성 갤럭시탭A8", 1000, 4.1, 900, 1),
        ProductData("레노버 탭P11", 800, 3.8, 800, 0),
        ProductData("화웨이 MatePad", 1200, 4.3, 950, 1),
        ProductData("샤오미 Pad5", 900, 4.0, 850, 0),
        ProductData("아마존 파이어HD", 600, 3.2, 700, 0),
        ProductData("ASUS 젠패드", 1100, 4.2, 920, 1)
    ]
    
    return {
        "노트북": notebook_products,
        "스마트폰": smartphone_products,
        "태블릿": tablet_products
    }

# =============================================================================
# AD_RANK 계산 함수들
# =============================================================================

def calculate_ad_rank(입찰가: int, 클릭전환율: float) -> float:
    """
    AD_RANK 계산
    
    AD_RANK 공식: 입찰가 × 클릭전환율(%)
    
    Args:
        입찰가 (int): 최대 입찰가 (원)
        클릭전환율 (float): 클릭 대비 전환율 (%)
    
    Returns:
        float: AD_RANK 점수
        
    Raises:
        ValueError: 입찰가가 음수이거나 클릭전환율이 음수인 경우
        
    예시:
        입찰가 2000원, 클릭전환율 5.1% → AD_RANK = 2000 × 0.051 = 102점
    """
    # 입력값 검증
    if 입찰가 < 0:
        raise ValueError("입찰가는 0 이상이어야 합니다.")
    if 클릭전환율 < 0:
        raise ValueError("클릭전환율은 0 이상이어야 합니다.")
    
    # CTR이 0인 경우 최소값 적용
    if 클릭전환율 == 0:
        클릭전환율 = AdRankConstants.MIN_CTR
        logging.warning(f"클릭전환율이 0인 경우 최소값 {AdRankConstants.MIN_CTR}% 적용")
    
    return 입찰가 * (클릭전환율 / 100)

def calculate_cpc(current_ad_rank: float, next_ad_rank: Optional[float], 
                 current_ctr: float, max_bid: int) -> int:
    """
    CPC (Cost Per Click) 계산
    
    CPC 공식: (다음 순위 AD_RANK / 본인 클릭전환율) + 1원
    
    Args:
        current_ad_rank (float): 현재 상품의 AD_RANK
        next_ad_rank (Optional[float]): 다음 순위 상품의 AD_RANK (None이면 마지막 순위)
        current_ctr (float): 현재 상품의 클릭전환율 (%)
        max_bid (int): 현재 상품의 최대 입찰가
    
    Returns:
        int: CPC (원)
        
    Raises:
        ValueError: 클릭전환율이 0인 경우
        
    예시:
        다음 순위 AD_RANK 45점, 본인 클릭전환율 5.0% → CPC = (45 / 0.05) + 1 = 901원
    """
    # 입력값 검증
    if current_ctr <= 0:
        raise ValueError("클릭전환율은 0보다 커야 합니다.")
    
    # 마지막 순위인 경우 최대 입찰가 반환
    if next_ad_rank is None:
        return max_bid
    
    # CPC 계산: (다음 순위 AD_RANK / 본인 클릭전환율) + 1원
    cpc = (next_ad_rank / (current_ctr / 100)) + AdRankConstants.CPC_ADDITION
    return int(cpc)

def calculate_bonus_points(노출수: int, 구매수: int) -> Tuple[int, int]:
    """
    가산점 계산
    
    가산점 기준:
    - 노출 기준치 가산점: 노출수 1,000회 이상 시 1점
    - 구매 전환 가산점: 구매수 1회 이상 시 1점
    
    Args:
        노출수 (int): 누적 노출 수
        구매수 (int): 노출 1,000회 동안 구매 수
    
    Returns:
        Tuple[int, int]: (노출_기준치_가산점, 구매_전환_가산점)
        
    예시:
        노출수 1200회, 구매수 2회 → (1, 1) = 총 2점 가산
        노출수 800회, 구매수 1회 → (0, 1) = 총 1점 가산
    """
    # 노출 기준치 가산점 (1000회 이상)
    노출_기준치_가산점 = 1 if 노출수 >= AdRankConstants.EXPOSURE_THRESHOLD else 0
    
    # 구매 전환 가산점 (1회 이상)
    구매_전환_가산점 = 1 if 구매수 >= AdRankConstants.PURCHASE_THRESHOLD else 0
    
    return 노출_기준치_가산점, 구매_전환_가산점

def calculate_exposure_ratio(ad_rank_scores: Dict[str, float]) -> Dict[str, float]:
    """
    노출 비중 계산
    
    노출 비중 공식: 각 상품의 AD_RANK / 전체 AD_RANK 합계
    30% 상한 제한: 단일 상품이 30%를 초과할 경우 30%로 제한하고 초과분을 재분배
    
    Args:
        ad_rank_scores (Dict[str, float]): 상품명을 키로, AD_RANK를 값으로 하는 딕셔너리
    
    Returns:
        Dict[str, float]: 상품명을 키로, 노출 비중(%)을 값으로 하는 딕셔너리
        
    계산 과정:
    1. 기본 비중 계산: 각 상품의 AD_RANK / 전체 합계
    2. 30% 상한 제한: 30% 초과 상품들을 30%로 제한
    3. 초과분 재분배: 초과분을 30% 미만 상품들에 비율에 따라 재분배
    4. 소수점 반올림: 최종 비중을 소수점 2자리로 반올림
    """
    if not ad_rank_scores:
        return {}
    
    total_score = sum(ad_rank_scores.values())
    if total_score == 0:
        return {product: 0.0 for product in ad_rank_scores}
    
    ratios = {}
    
    # 1단계: 기본 비중 계산
    for product, score in ad_rank_scores.items():
        ratio = (score / total_score) * 100
        ratios[product] = ratio
    
    # 2단계: 30% 상한 제한 및 초과분 계산
    excess_total = 0
    for product in ratios:
        if ratios[product] > AdRankConstants.MAX_EXPOSURE_RATIO:
            excess = ratios[product] - AdRankConstants.MAX_EXPOSURE_RATIO
            ratios[product] = AdRankConstants.MAX_EXPOSURE_RATIO
            excess_total += excess
    
    # 3단계: 초과분을 30% 미만 상품들에 재분배
    if excess_total > 0:
        eligible_products = [p for p in ratios if ratios[p] < AdRankConstants.MAX_EXPOSURE_RATIO]
        if eligible_products:
            eligible_total = sum(ratios[p] for p in eligible_products)
            for product in eligible_products:
                if eligible_total > 0:
                    redistribution = (ratios[product] / eligible_total) * excess_total
                    ratios[product] += redistribution
    
    # 4단계: 소수점 2자리로 반올림
    for product in ratios:
        ratios[product] = round(ratios[product], AdRankConstants.DECIMAL_PLACES)
    
    return ratios

# =============================================================================
# 유틸리티 함수들
# =============================================================================

def _get_bonus_description(노출_가산점: int, 구매_가산점: int) -> str:
    """
    가산점 설명 문자열 생성
    
    Args:
        노출_가산점 (int): 노출 기준치 가산점 (0 또는 1)
        구매_가산점 (int): 구매 전환 가산점 (0 또는 1)
    
    Returns:
        str: 가산점 설명 문자열
    """
    if 노출_가산점 == 1 and 구매_가산점 == 1:
        return "노출+구매"
    elif 노출_가산점 == 1:
        return "노출만"
    elif 구매_가산점 == 1:
        return "구매만"
    else:
        return "없음"

def _print_ranking_results(results: List[AdRankResult], category_name: str) -> None:
    """
    AD_RANK 랭킹 결과 출력
    
    Args:
        results (List[AdRankResult]): AD_RANK 계산 결과 리스트
        category_name (str): 카테고리명
    """
    print(f"\n{'='*100}")
    print(f"📊 {category_name} 카테고리 AD_RANK 랭킹 결과")
    print(f"{'='*100}")
    
    # 헤더 출력
    print(f"{'순위':<4} {'상품명':<20} {'입찰가':<8} {'CTR':<6} {'AD_RANK':<10} {'가산점':<8} {'최종점수':<10} {'CPC':<8} {'노출비중':<8}")
    print("-" * 100)
    
    # 상위 20개만 출력 (너무 많으면 가독성 떨어짐)
    display_count = min(20, len(results))
    
    for i, result in enumerate(results[:display_count], 1):
        bonus_desc = _get_bonus_description(result.노출_가산점, result.구매_가산점)
        
        print(f"{i:<4} {result.상품명:<20} {result.입찰가:<8} {result.클릭전환율:<6.1f}% "
              f"{result.AD_RANK:<10.2f} {bonus_desc:<8} {result.최종_점수:<10.2f} "
              f"{result.CPC:<8} {result.노출_비중:<8.2f}%")
    
    if len(results) > display_count:
        print(f"\n... 외 {len(results) - display_count}개 상품")
    
    # 통계 요약
    print(f"\n{'='*60}")
    print("📈 랭킹 통계 요약")
    print(f"{'='*60}")
    
    if results:
        # AD_RANK 통계
        ad_ranks = [r.AD_RANK for r in results]
        print(f"AD_RANK 최고점: {max(ad_ranks):.2f}점")
        print(f"AD_RANK 최저점: {min(ad_ranks):.2f}점")
        print(f"AD_RANK 평균: {sum(ad_ranks)/len(ad_ranks):.2f}점")
        
        # CPC 통계
        cpcs = [r.CPC for r in results]
        print(f"CPC 최고: {max(cpcs)}원")
        print(f"CPC 최저: {min(cpcs)}원")
        print(f"CPC 평균: {sum(cpcs)/len(cpcs):.0f}원")
        
        # 노출 비중 통계
        exposure_ratios = [r.노출_비중 for r in results]
        print(f"노출 비중 최고: {max(exposure_ratios):.2f}%")
        print(f"노출 비중 최저: {min(exposure_ratios):.2f}%")
        
        # 가산점 통계
        total_bonus = sum(r.노출_가산점 + r.구매_가산점 for r in results)
        print(f"총 가산점: {total_bonus}점 (상품당 평균 {total_bonus/len(results):.2f}점)")
    
    # 노출 비중별 가중 랜덤 선택
    _print_weighted_random_selection(results, category_name)

def _print_weighted_random_selection(results: List[AdRankResult], category_name: str) -> None:
    """
    노출 비중별 가중 랜덤 선택 결과 출력
    
    Args:
        results (List[AdRankResult]): AD_RANK 계산 결과 리스트
        category_name (str): 카테고리명
    """
    print(f"\n{'='*80}")
    print(f"🎲 {category_name} 카테고리 노출 비중별 가중 랜덤 선택 (10개)")
    print(f"{'='*80}")
    
    if not results:
        print("선택할 상품이 없습니다.")
        return
    
    # 노출 비중이 0보다 큰 상품들만 필터링
    valid_products = [r for r in results if r.노출_비중 > 0]
    
    if not valid_products:
        print("노출 비중이 0인 상품만 있어서 선택할 수 없습니다.")
        return
    
    # 가중치로 사용할 노출 비중 추출
    weights = [product.노출_비중 for product in valid_products]
    product_names = [product.상품명 for product in valid_products]
    
    # 중복 없이 10개 선택 (가능한 최대 개수만큼)
    selection_count = min(10, len(valid_products))
    
    try:
        # 가중 랜덤 선택 (중복 허용)
        selected_indices = random.choices(
            range(len(valid_products)), 
            weights=weights, 
            k=selection_count
        )
        
        # 중복 제거 (순서 유지)
        unique_indices = []
        seen = set()
        for idx in selected_indices:
            if idx not in seen:
                unique_indices.append(idx)
                seen.add(idx)
        
        # 중복 제거 후 부족한 경우 추가 선택
        while len(unique_indices) < selection_count and len(unique_indices) < len(valid_products):
            remaining_products = [i for i in range(len(valid_products)) if i not in seen]
            if not remaining_products:
                break
            
            remaining_weights = [weights[i] for i in remaining_products]
            additional_idx = random.choices(remaining_products, weights=remaining_weights, k=1)[0]
            unique_indices.append(additional_idx)
            seen.add(additional_idx)
        
        # 최종 선택된 상품들
        selected_products = [valid_products[i] for i in unique_indices]
        
        # 결과 출력
        print(f"노출 비중에 따른 가중 랜덤 선택 결과 ({len(selected_products)}개):")
        print("-" * 80)
        print(f"{'순번':<4} {'상품명':<25} {'노출비중':<10} {'AD_RANK':<10} {'CPC':<8}")
        print("-" * 80)
        
        total_weight = sum(weights)
        for i, product in enumerate(selected_products, 1):
            selection_probability = (product.노출_비중 / total_weight) * 100
            print(f"{i:<4} {product.상품명:<25} {product.노출_비중:<10.2f}% {product.AD_RANK:<10.2f} {product.CPC:<8}")
        
        # 선택 통계
        print(f"\n{'='*50}")
        print("🎯 선택 통계")
        print(f"{'='*50}")
        
        selected_weights = [p.노출_비중 for p in selected_products]
        print(f"선택된 상품들의 노출 비중 합계: {sum(selected_weights):.2f}%")
        print(f"전체 상품들의 노출 비중 합계: {total_weight:.2f}%")
        print(f"선택 비율: {(sum(selected_weights) / total_weight) * 100:.2f}%")
        print(f"평균 노출 비중: {sum(selected_weights) / len(selected_products):.2f}%")
        
        # 선택된 상품들의 AD_RANK 통계
        selected_ad_ranks = [p.AD_RANK for p in selected_products]
        print(f"선택된 상품들의 AD_RANK 평균: {sum(selected_ad_ranks) / len(selected_ad_ranks):.2f}점")
        print(f"전체 상품들의 AD_RANK 평균: {sum(r.AD_RANK for r in results) / len(results):.2f}점")
        
    except Exception as e:
        print(f"가중 랜덤 선택 중 오류 발생: {e}")
        # 오류 시 단순 랜덤 선택으로 대체
        print("단순 랜덤 선택으로 대체합니다.")
        simple_selection = random.sample(valid_products, min(10, len(valid_products)))
        
        print(f"단순 랜덤 선택 결과 ({len(simple_selection)}개):")
        print("-" * 80)
        print(f"{'순번':<4} {'상품명':<25} {'노출비중':<10} {'AD_RANK':<10} {'CPC':<8}")
        print("-" * 80)
        
        for i, product in enumerate(simple_selection, 1):
            print(f"{i:<4} {product.상품명:<25} {product.노출_비중:<10.2f}% {product.AD_RANK:<10.2f} {product.CPC:<8}")

def _get_performance_grade(processing_time_ms: float) -> str:
    """
    성능 등급 반환
    
    Args:
        processing_time_ms (float): 처리 시간 (ms)
    
    Returns:
        str: 성능 등급 (우수/양호/허용/불량)
    """
    if processing_time_ms <= AdRankConstants.PERFORMANCE_EXCELLENT:
        return "우수 🚀"
    elif processing_time_ms <= AdRankConstants.PERFORMANCE_GOOD:
        return "양호 ✅"
    elif processing_time_ms <= AdRankConstants.PERFORMANCE_ACCEPTABLE:
        return "허용 ⚠️"
    else:
        return "불량 ❌"

def _print_performance_summary(metrics: PerformanceMetrics) -> None:
    """
    성능 요약 출력
    
    Args:
        metrics (PerformanceMetrics): 성능 측정 결과
    """
    print(f"\n{'='*60}")
    print("성능 요약")
    print(f"{'='*60}")
    
    # 기본 성능 정보
    print(f"총 처리 시간: {metrics.처리_시간_ms:.2f}ms")
    print(f"총 상품 수: {metrics.총_상품_수}개")
    print(f"카테고리 수: {metrics.카테고리_수}개")
    print(f"평균 카테고리 처리 시간: {metrics.평균_카테고리_처리시간_ms:.2f}ms")
    print(f"상품당 평균 처리 시간: {metrics.상품당_평균_처리시간_ms:.4f}ms")
    
    # 1초와 비교하는 성능 분석
    print(f"\n{'='*40}")
    print("1초 대비 성능 분석")
    print(f"{'='*40}")
    
    # 1초와의 차이 계산
    one_second_ms = 1000.0
    time_diff_ms = one_second_ms - metrics.처리_시간_ms
    time_ratio = (metrics.처리_시간_ms / one_second_ms) * 100
    
    print(f"1초(1000ms) 대비: {time_diff_ms:.2f}ms {'빠름' if time_diff_ms > 0 else '느림'}")
    print(f"1초 대비 비율: {time_ratio:.3f}%")
    
    # 성능 등급 평가
    performance_grade = _get_performance_grade(metrics.처리_시간_ms)
    print(f"성능 등급: {performance_grade}")
    
    # 직관적 비교
    if metrics.처리_시간_ms < 1.0:
        print(f"💡 {metrics.처리_시간_ms:.2f}ms는 1초보다 약 {one_second_ms/metrics.처리_시간_ms:.0f}배 빠름")
    elif metrics.처리_시간_ms > 1000.0:
        print(f"💡 {metrics.처리_시간_ms:.2f}ms는 1초보다 약 {metrics.처리_시간_ms/one_second_ms:.1f}배 느림")
    else:
        print(f"💡 {metrics.처리_시간_ms:.2f}ms는 1초의 {time_ratio:.1f}% 수준")

# =============================================================================
# 메인 처리 함수들
# =============================================================================

def process_category_ranking(category_name: str, products: List[ProductData]) -> Tuple[List[AdRankResult], float]:
    """
    카테고리별 AD_RANK 처리 (독립 처리)
    
    AD_RANK 요구사항에 따라 카테고리별로 상품 랭킹을 계산합니다.
    
    Args:
        category_name (str): 카테고리명
        products (List[ProductData]): 상품 데이터 리스트
    
    Returns:
        Tuple[List[AdRankResult], float]: 
            (전체_결과, 처리_시간)
    
    처리 과정:
    1. AD_RANK 계산: 입찰가 × 클릭전환율
    2. 가산점 계산: 노출 1000회 + 구매 1회
    3. 최종 점수 계산: AD_RANK + 가산점
    4. 내림차순 정렬
    5. CPC 계산: (다음 순위 AD_RANK / 본인 클릭전환율) + 1
    6. 노출 비중 계산: AD_RANK 기반 (30% 상한 제한)
    """
    
    print(f"\n카테고리: {category_name}")
    print(f"{'='*50}")
    
    start_time = time.time()
    
    # 1단계: AD_RANK 계산 및 가산점 적용
    results = []
    for product in products:
        try:
            # AD_RANK 계산: 입찰가 × 클릭전환율
            ad_rank = calculate_ad_rank(product.입찰가, product.클릭전환율)
            
            # 가산점 계산: 노출 1000회 + 구매 1회
            노출_가산점, 구매_가산점 = calculate_bonus_points(product.노출수, product.구매수)
            
            # 결과 데이터 구성
            result = AdRankResult(
                상품명=product.상품명,
                입찰가=product.입찰가,
                클릭전환율=product.클릭전환율,
                노출수=product.노출수,
                구매수=product.구매수,
                AD_RANK=round(ad_rank, AdRankConstants.DECIMAL_PLACES),
                노출_가산점=노출_가산점,
                구매_가산점=구매_가산점,
                최종_점수=round(ad_rank + 노출_가산점 + 구매_가산점, AdRankConstants.DECIMAL_PLACES),
                CPC=0,  # 나중에 계산
                노출_비중=0.0  # 나중에 계산
            )
            results.append(result)
            
        except ValueError as e:
            logging.error(f"상품 {product.상품명} 처리 중 오류: {e}")
            continue
    
    # 2단계: 최종 점수 기준 내림차순 정렬
    results.sort(key=lambda x: x.최종_점수, reverse=True)
    
    # 3단계: CPC 계산 (다음 순위 AD_RANK / 본인 클릭전환율 + 1)
    for i, result in enumerate(results):
        try:
            if i < len(results) - 1:
                next_ad_rank = results[i + 1].AD_RANK
            else:
                next_ad_rank = None  # 마지막 순위는 최대 입찰가 사용
            
            cpc = calculate_cpc(
                result.AD_RANK, 
                next_ad_rank, 
                result.클릭전환율, 
                result.입찰가
            )
            result.CPC = cpc
            
        except ValueError as e:
            logging.error(f"상품 {result.상품명} CPC 계산 중 오류: {e}")
            result.CPC = result.입찰가  # 오류 시 최대 입찰가 사용
    
    # 4단계: 노출 비중 계산 (AD_RANK 기반, 30% 상한 제한)
    ad_rank_scores = {r.상품명: r.AD_RANK for r in results}
    exposure_ratios = calculate_exposure_ratio(ad_rank_scores)
    
    for result in results:
        result.노출_비중 = round(exposure_ratios[result.상품명], AdRankConstants.DECIMAL_PLACES)
    
    # 5단계: 결과 출력
    _print_ranking_results(results, category_name)
    
    # 처리 시간 계산
    end_time = time.time()
    processing_time = (end_time - start_time) * 1000  # ms 변환
    
    # 성능 등급과 함께 출력
    performance_grade = _get_performance_grade(processing_time)
    print(f"\n처리 시간: {processing_time:.2f}ms ({performance_grade})")
    
    return results, processing_time

def main() -> None:
    """
    메인 실행 함수
    
    AD_RANK 광고 엔진의 전체 처리 과정을 실행합니다.
    
    처리 플로우:
    1. 카테고리 선택
    2. 선택된 카테고리의 AD_RANK 처리
    3. 성능 요약 출력
    """
    
    # 로깅 설정
    setup_logging()
    
    print("AD_RANK 광고 엔진 결과 (카테고리별 독립 처리)")
    print("=" * 60)
    
    try:
        print("\n" + "="*50)
        print("카테고리 선택")
        print("="*50)
        print("1. 노트북 (100개 상품)")
        print("2. 스마트폰 (19개 상품)")
        print("3. 태블릿 (10개 상품)")
        print("-"*50)
        
        # 1단계: 카테고리 선택
        selected_category = "노트북"
        
        # 2단계: 샘플 데이터 생성
        categories = generate_sample_data()
        
        if selected_category not in categories:
            print(f"❌ 선택한 카테고리 '{selected_category}'를 찾을 수 없습니다.")
            return
        
        products = categories[selected_category]
        print(f"\n선택된 카테고리: {selected_category} ({len(products)}개 상품)")
        
        # 3단계: 선택된 카테고리 처리
        total_start_time = time.time()
        
        try:
            results, processing_time = process_category_ranking(selected_category, products)
            
            # 4단계: 성능 요약 출력
            print(f"\n{'='*60}")
            print(f"{selected_category} 카테고리 성능 요약")
            print(f"{'='*60}")
            metrics = PerformanceMetrics(
                처리_시간_ms=processing_time,
                총_상품_수=len(products),
                카테고리_수=1,
                평균_카테고리_처리시간_ms=processing_time,
                상품당_평균_처리시간_ms=processing_time/len(products) if len(products) > 0 else 0
            )
            _print_performance_summary(metrics)
            
        except Exception as e:
            logging.error(f"카테고리 {selected_category} 처리 중 오류: {e}")
            return
        
        total_end_time = time.time()
        total_processing_time = (total_end_time - total_start_time) * 1000
        
        print(f"\n{'='*60}")
        print("전체 처리 완료")
        print(f"{'='*60}")
        print(f"총 처리 시간: {total_processing_time:.2f}ms")
        print(f"선택된 카테고리: {selected_category}")
        print(f"처리된 상품 수: {len(products)}개")
        
        logging.info("AD_RANK 광고 엔진 처리 완료")
        
    except Exception as e:
        logging.error(f"메인 처리 중 오류 발생: {e}")
        raise

if __name__ == "__main__":
    main()