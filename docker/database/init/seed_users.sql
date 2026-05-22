-- users + oauth_accounts 샘플 데이터 100건
DO $$
DECLARE
    uid       uuid;
    i         int;
    p         text;
    s         text;
    r         text;
    email_val text;
    disp_val  text;

    providers text[] := ARRAY['kakao','google','naver','kakao','google','naver','kakao','google','facebook','naver'];
    domains   text[] := ARRAY['gmail.com','naver.com','kakao.com','daum.net','hanmail.net','outlook.com','icloud.com','yahoo.com'];
    statuses  text[] := ARRAY['active','active','active','active','active','active','active','active','suspended','deleted'];

    sur_names text[] := ARRAY[
        '김','이','박','최','정','강','조','윤','장','임',
        '한','오','서','신','권','황','안','송','류','홍',
        '전','고','문','양','손','배','백','허','노','남',
        '심','원','천','방','공','석','표','마','가','나'
    ];
    giv_names text[] := ARRAY[
        '민준','서준','예준','도윤','시우','주원','지호','지후','준서','준우',
        '지안','서연','서윤','지유','지민','수아','하은','하린','나은','지원',
        '재원','지훈','태양','다인','가연','은서','아름','수빈','지혜','민지',
        '현우','성민','유진','예린','소현','민호','지영','태희','지연','민수'
    ];

    -- 이메일용 영문 이름 100개
    eng_ids text[] := ARRAY[
        'minjun.kim','seojun.lee','yejun.park','doyun.choi','siwoo.jung',
        'juwon.kang','jiho.cho','jihoo.yoon','junser.jang','junwoo.im',
        'jian.han','seoyeon.oh','seoyoon.seo','jiyu.shin','jimin.kwon',
        'sua.hwang','haeun.an','harin.song','naeun.ryu','jiwon.hong',
        'jaewon.jeon','jihun.ko','taeyang.moon','dain.yang','gayeon.son',
        'eunseo.bae','areum.baek','subin.heo','jihye.noh','minji.nam',
        'hyunwoo.sim','sungmin.won','yujin.cheon','yerin.bang','sohyeon.gong',
        'minho.seok','jiyoung.pyo','taehee.ma','jiyeon.ga','minsoo.na',
        'yuna.kim2','hyunki.lee2','sora.park2','junho.choi2','eunjin.jung2',
        'sungho.kang2','hyemi.cho2','jinho.yoon2','yejin.jang2','junho.im2',
        'suji.han2','kyungmin.oh2','jisoo.seo2','minah.shin2','jihyun.kwon2',
        'seungwon.hwang2','yoonji.an2','sangwoo.song2','hyunjin.ryu2','minhee.hong2',
        'jieun.jeon2','somin.ko2','seohyun.moon2','youngjin.yang2','nakyung.son2',
        'mirae.bae2','jungsoo.baek2','taejun.heo2','eunji.noh2','sungwoo.nam2',
        'jihee.sim2','inyoung.won2','dongwoo.cheon2','sinae.bang2','hyunseok.gong2',
        'seulgi.seok2','junhyuk.pyo2','minyoung.ma2','donghyun.kim3','hayeon.lee3',
        'seunggi.park3','boyoung.choi3','jaeyoon.jung3','sooyeon.kang3','hyunwoo.cho3',
        'yujung.yoon3','seoyun.jang3','jihwan.im3','nayoung.han3','dongjun.oh3',
        'heejin.seo3','minhyuk.shin3','jungwoo.kwon3','hyejin.hwang3','taemin.an3',
        'soojin.song3','hwijae.ryu3','sera.hong3','jungmin.jeon3','hyunki.ko3'
    ];
BEGIN
    FOR i IN 1..100 LOOP
        uid       := gen_random_uuid();
        p         := providers[((i - 1) % array_length(providers, 1)) + 1];
        s         := statuses[((i - 1)  % array_length(statuses,  1)) + 1];
        r         := 'user';

        -- 처음 3명은 admin / active 고정
        IF i <= 3 THEN
            r := 'admin';
            s := 'active';
        END IF;

        disp_val  := sur_names[((i - 1) % array_length(sur_names, 1)) + 1]
                  || giv_names[((i - 1) % array_length(giv_names, 1)) + 1];
        email_val := eng_ids[i] || '@' || domains[((i - 1) % array_length(domains, 1)) + 1];

        INSERT INTO users (
            user_id, email, display_name, role, status, created_at, updated_at
        ) VALUES (
            uid,
            email_val,
            disp_val,
            r,
            s,
            NOW() - ((floor(random() * 500) + 1)::text || ' days')::interval,
            NOW() - ( floor(random() * 30)   ::text || ' days')::interval
        );

        INSERT INTO oauth_accounts (
            user_id, provider, provider_user_id,
            provider_email, provider_name, linked_at, last_used_at
        ) VALUES (
            uid,
            p,
            p || '_' || ((floor(random() * 9000000) + 1000000)::bigint)::text,
            email_val,
            disp_val,
            NOW() - ((floor(random() * 500) + 1)::text || ' days')::interval,
            NOW() - ( floor(random() * 14)   ::text || ' days')::interval
        );
    END LOOP;
END $$;
