;=============================================================================
; GRAND THEFT TRABANT VI – BALATON VICE
; paródia-"trailer" demó Videoton TV-Computer 64K-ra, 16 színű mód (128x240)
; Z80 @ 3.125 MHz, sjasmplus. Indítás: 10 PRINT USR(6659), automatikusan.
;
; Jelenetek: KŐSZTÁR GAMES bemutatja -> naplemente a Balatonon -> üldözés
; Siófok mellett -> komp Tihanyba -> címkép -> a megjelenési dátumok csúszása.  Körbe megy.
; Szóköz: következő jelenet,  Esc: kilépés a BASIC-be.
;
; Memória (lapozás $90 = U0 | U1 | VID | U3):
;   $19EF-$7FFF  BASIC betöltő, kód, adatok
;   $8000-$BBFF  képernyő, 64 bájt/sor
;   $C000-       változók, verem (U3 teteje)
; Megszakítás tiltva; a képkocka-ütemezés a $59-es port 4. bitjét figyeli.
;=============================================================================

        DEVICE NOSLOT64K

VRAM        equ $8000
P_SAVE      equ $0003
PORT03      equ $0B11           ; ROM-másolatok a kilépéshez
PORT05      equ $0B12
PORT06      equ $0B13
INKV        equ $0B4D
PAPERV      equ $0B4E
BORDERV     equ $0B4F
MAP_DEMO    equ $90

K_SPACE     equ $04             ; keys+1
K_ESC       equ $08

SKYN        equ SKY1-SKY0+1
SKYHALF     equ SKYN/2

;-----------------------------------------------------------------------------
; BASIC betöltő: 10 PRINT USR(6659)
;-----------------------------------------------------------------------------
        ORG $19EF
        db $0F,$0A,$00,$DD
        db " USR"
        db $96
        db "6659"
        db $95,$FF
        db 0,0,0,0,0
        ASSERT $ == 6659

;=============================================================================
start:
        di
        ld (quit_sp+1),sp
        ld a,MAP_DEMO
        ld (P_SAVE),a
        out ($02),a
        ld sp,0                 ; verem az U3 tetején
        xor a
        out ($05),a             ; hang ki
        out ($03),a
        out ($00),a             ; keret: fekete
        ld a,2
        out ($06),a             ; 16 színű mód
        ld hl,BSS
        ld de,BSS+1
        ld bc,BSS_LEN-1
        ld (hl),0
        ldir
.again: call scene_splash
        call scene_sunset
        call scene_chase
        call scene_ferry
        call scene_title
        call scene_delay
        jr .again

;=============================================================================
; KÖZÖS: jelenet indítása, képkocka-ütem, feliratok
;=============================================================================
; scene_start: HL = felirat-idővonal, DE = jelenet hossza (képkocka)
scene_start:
        ld (cap_ptr),hl
        ld (scene_len),de
        ld hl,0
        ld (frame),hl
        xor a
        ld (tw_on),a
        ret

; tick: egy képkocka. C = vége a jelenetnek (szóköz vagy lejárt az idő)
tick:
        call vsync
        call snd_tick
        call read_keys
        ld a,(knew+1)
        and K_ESC
        jp nz,quit
        call cap_check
        call tw_step
        ld hl,(frame)
        inc hl
        ld (frame),hl
        ld a,(knew+1)
        and K_SPACE
        jr nz,.end
        ld de,(scene_len)
        or a
        sbc hl,de
        jr nc,.end
        or a
        ret
.end:   scf
        ret

; wait: B képkocka; C = vége a jelenetnek
wait:   push bc
        call tick
        pop bc
        ret c
        djnz wait
        or a
        ret

; cap_check: ha elérkezett a következő felirat ideje, letörli a sort és elindítja a gépelést
cap_check:
        ld hl,(cap_ptr)
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld hl,(frame)
        or a
        sbc hl,de
        ret nz
        ld hl,(cap_ptr)
        inc hl
        inc hl
        ld e,(hl) : inc hl : ld d,(hl) : inc hl
        ld (tw_src),de
        ld e,(hl) : inc hl : ld d,(hl) : inc hl
        ld (tw_dst),de
        ld e,(hl) : inc hl : ld d,(hl) : inc hl
        ld (tw_nib),de
        ld (cap_ptr),hl
        ld hl,VRAM+CAP_Y*64
        ld de,VRAM+CAP_Y*64+1
        ld bc,12*64-1
        ld (hl),0
        ldir
        ld a,1
        ld (tw_on),a
        ld (tw_cnt),a
        ret

; tw_step: gépelős felirat, 2 képkockánként egy betű
tw_step:
        ld a,(tw_on)
        or a
        ret z
        ld hl,tw_cnt
        dec (hl)
        ret nz
        ld (hl),2
        ld hl,(tw_src)
        ld a,(hl)
        cp $FF
        jr z,.end
        inc hl
        ld (tw_src),hl
        ld hl,(tw_nib)
        ld (cur_nib),hl
        ld de,(tw_dst)
        call print_glyph
        ld (tw_dst),de
        ret
.end:   xor a
        ld (tw_on),a
        ret

;=============================================================================
; RAJZOLÓ RUTINOK
;=============================================================================
cls_all:
        ld hl,VRAM
        ld de,VRAM+1
        ld bc,240*64-1
        ld (hl),0
        ldir
        ret

; show_img: HL = tömörített kép (214 sor), a felirat-sáv fekete marad
show_img:
        push hl
        call cls_all
        pop hl
        ld de,VRAM
        ld bc,IMG_LEN
        ; tovább: unrle

; unrle: HL = forrás, DE = cél, BC = kibontott hossz
unrle:
        ld (ur_left),bc
.loop:  ld bc,(ur_left)
        ld a,b
        or c
        ret z
        ld a,(hl)
        inc hl
        cp 128
        jr nc,.run
        inc a                   ; nyers: 1..128 bájt
        ld c,a
        ld b,0
        call .dec
        ldir
        jr .loop
.run:   sub 125                 ; ismétlés: 3..130 bájt
        ld c,a
        ld b,0
        call .dec
        ld a,(hl)
        inc hl
        push hl
        ld h,d
        ld l,e
        ld (hl),a
        inc de
        dec c
        jr z,.one
        ldir                    ; önmagára másolva tölti ki
.one:   pop hl
        jr .loop
.dec:   push hl                 ; ur_left -= BC
        ld hl,(ur_left)
        or a
        sbc hl,bc
        ld (ur_left),hl
        pop hl
        ret

; blit: HL = forrás, DE = képernyőcím, B = szélesség, C = magasság, (bl_stride) = forrás sorhossza
blit:
.r:     push bc
        push hl
        push de
        ld c,b
        ld b,0
        ldir
        pop hl
        ld bc,64
        add hl,bc
        ex de,hl
        pop hl
        ld bc,(bl_stride)
        add hl,bc
        pop bc
        dec c
        jr nz,.r
        ret

; blit_w: mint blit, de a forrás sorhossza = B
blit_w:
        push hl
        ld l,b
        ld h,0
        ld (bl_stride),hl
        pop hl
        jr blit

; fill_rect: HL = cím, B = szélesség, C = magasság, A = bájt
fill_rect:
.r:     push bc
        push hl
.c:     ld (hl),a
        inc hl
        djnz .c
        pop hl
        ld de,64
        add hl,de
        pop bc
        dec c
        jr nz,.r
        ret

; print_glyph: A = jel, DE = cím, (cur_nib) = színtábla; DE += 2. Rontja: AF, BC, HL
print_glyph:
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        ld b,h
        ld c,l
        add hl,hl
        add hl,bc               ; *12
        ld bc,FONT
        add hl,bc
        push de
        ld b,12
.r:     ld a,(hl)
        inc hl
        push hl
        ld hl,(cur_nib)
        add a,l
        ld l,a
        jr nc,$+3
        inc h
        ld a,(hl)
        ld (de),a
        inc hl
        inc de
        ld a,(hl)
        ld (de),a
        ex de,hl
        ld de,63
        add hl,de
        ex de,hl
        pop hl
        djnz .r
        pop de
        inc de
        inc de
        ret

; print_str: HL = szöveg ($FF a vége), DE = cím
print_str:
        ld a,(hl)
        cp $FF
        ret z
        push hl
        call print_glyph
        pop hl
        inc hl
        jr print_str

; print_big_glyph: dupla széles és magas jel (4 bájt x 24 sor); (cur_big) = színtábla
print_big_glyph:
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        ld b,h
        ld c,l
        add hl,hl
        add hl,bc
        ld bc,FONT
        add hl,bc
        push de
        ld b,12
.r:     push bc
        ld a,(hl)
        inc hl
        push hl
        add a,a                 ; a táblában 4 bájt / érték
        ld hl,(cur_big)
        add a,l
        ld l,a
        jr nc,$+3
        inc h
        ex de,hl                ; HL = cél, DE = táblaelem
        ld c,4
.c:     ld a,(de)
        inc de
        ld (hl),a
        push de
        ld de,64
        add hl,de
        ld (hl),a
        ld de,-63
        add hl,de
        pop de
        dec c
        jr nz,.c
        ld de,124
        add hl,de
        ex de,hl
        pop hl
        pop bc
        djnz .r
        pop de
        inc de
        inc de
        inc de
        inc de
        ret

print_big_str:
        ld a,(hl)
        cp $FF
        ret z
        push hl
        call print_big_glyph
        pop hl
        inc hl
        jr print_big_str

;=============================================================================
; 0. KŐSZTÁR GAMES BEMUTATJA
;=============================================================================
scene_splash:
        call snd_stop
        call cls_all
        ld hl,CAP_NONE
        ld de,SPLASH_FADE_N*8+30
        call scene_start
.loop:  call tick
        ret c
        ld a,(frame)
        and 7
        cp 1
        jr nz,.loop
        ld a,(frame)
        rrca
        rrca
        rrca
        and 31
        cp SPLASH_FADE_N
        jr nc,.loop
        add a,a
        ld l,a
        ld h,0
        ld de,SPLASH_FADE
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld (cur_big),de
        ld hl,SPL1_STR
        ld de,SPL1_ADDR
        call print_big_str
        ld hl,SPL2_STR
        ld de,SPL2_ADDR
        call print_big_str
        jr .loop

;=============================================================================
; 1. NAPLEMENTE A BALATONON
;=============================================================================
scene_sunset:
        ld hl,IMG_SUNSET
        call show_img
        ld a,40
        ld (sun_y),a
        ld a,1
        ld (sun_cnt),a
        ld a,$FF
        ld (sign_st),a
        call draw_sun
        ld hl,MUSIC
        call play_music
        ld hl,CAP_SUNSET
        ld de,800
        call scene_start
.loop:  call tick
        ret c
        ld hl,sun_cnt           ; a nap 6 képkockánként egy sort süllyed
        dec (hl)
        jr nz,.nos
        ld (hl),6
        ld a,(sun_y)
        cp HORIZON+SUN_R+1
        jr nc,.nos
        inc a
        ld (sun_y),a
        call draw_sun
        jr .sgn
.nos:   ld a,(frame)
        and 3
        call z,draw_refl
.sgn:
        ; LÁNGOS neon: villogási minta
        ld a,(frame)
        rrca
        rrca
        and 63
        ld hl,BLINK
        add a,l
        ld l,a
        jr nc,$+3
        inc h
        ld a,(hl)
        ld hl,sign_st
        cp (hl)
        jr z,.loop
        ld (hl),a
        ld hl,SIGN_OFF
        or a
        jr z,$+5
        ld hl,SIGN_ON
        ld de,SIGN_ADDR
        ld bc,SIGN_W*256+SIGN_H
        call blit_w
        jr .loop

; draw_sun: a nap oszlopait (24..40. bájt) újrarajzolja a sun_y körül, a horizontig
draw_sun:
        ld a,(sun_y)
        sub SUN_R+1
        ld (ds_y),a
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld de,VRAM+SKY_SUNCOL
        add hl,de
        ld (ds_addr),hl
        ld hl,SUNTAB
        ld (ds_tab),hl
        ld b,2*SUN_R+2
.row:   push bc
        ld a,(ds_y)
        cp HORIZON
        jr nc,.done
        ld l,a
        ld h,0
        ld de,SKYROW
        add hl,de
        ld a,(hl)
        ld hl,(ds_addr)
        REPT 16
        ld (hl),a
        inc hl
        ENDR
        ld (hl),a
        ld hl,(ds_tab)
        ld a,(hl)
        inc hl
        ld c,(hl)
        inc hl
        ld e,(hl)
        inc hl
        ld (ds_tab),hl
        ld b,c
        inc b
        dec b
        jr z,.next
        ld hl,(ds_addr)
        add a,l
        ld l,a
        jr nc,$+3
        inc h
        ld a,e
.s:     ld (hl),a
        inc hl
        djnz .s
.next:  ld hl,(ds_addr)
        ld de,64
        add hl,de
        ld (ds_addr),hl
        ld hl,ds_y
        inc (hl)
        pop bc
        djnz .row
        ret
.done:  pop bc
        ret

; draw_refl: a nap tükröződése a vízen, hullámzó szélességgel
draw_refl:
        ld a,(sun_y)
        ld l,a
        ld h,0
        ld de,FLEV
        add hl,de
        ld l,(hl)
        ld h,0
        ld d,h
        ld e,l
        add hl,hl
        add hl,hl
        add hl,de
        add hl,hl
        add hl,hl
        add hl,de               ; 21*f
        ld de,REFW
        add hl,de
        ld (rf_w),hl
        ld hl,VRAM+REFL_Y0*64+16
        ld (rf_addr),hl
        ld a,(frame)
        rrca
        rrca
        ld (rf_t),a
        ld b,0
.row:   push bc
        ld hl,WATROW
        ld a,b
        add a,l
        ld l,a
        jr nc,$+3
        inc h
        ld a,(hl)
        ld hl,(rf_addr)
        ld b,33
.f:     ld (hl),a
        inc hl
        djnz .f
        pop bc
        push bc
        ld a,b
        add a,a
        add a,b
        ld c,a
        ld a,(rf_t)
        add a,c
        and 15
        ld hl,WOB
        add a,l
        ld l,a
        jr nc,$+3
        inc h
        ld c,(hl)               ; hullám
        ld hl,(rf_w)
        ld a,b
        add a,l
        ld l,a
        jr nc,$+3
        inc h
        ld a,(hl)               ; alapszélesség
        or a
        jr z,.next
        add a,c
        bit 7,a
        jr nz,.next
        or a
        jr z,.next
        cp 17
        jr c,.ok
        ld a,16
.ok:    ld c,a
        ld a,16
        sub c
        ld hl,(rf_addr)
        add a,l
        ld l,a
        jr nc,$+3
        inc h
        push hl
        ld hl,REFB
        ld a,b
        add a,l
        ld l,a
        jr nc,$+3
        inc h
        ld a,(hl)
        pop hl
        sla c
        ld b,c
.s:     ld (hl),a
        inc hl
        djnz .s
.next:  ld hl,(rf_addr)
        ld de,64*3
        add hl,de
        ld (rf_addr),hl
        pop bc
        inc b
        ld a,b
        cp REFL_N
        jr c,.row
        ret

;=============================================================================
; 2. ÜLDÖZÉS A PARTI ÚTON
;=============================================================================
scene_chase:
        ld hl,IMG_CHASE
        call show_img
        ld hl,NIB_15_1
        ld (cur_nib),hl
        ld hl,HUD_TIME_STR
        ld de,HUD_TIME_ADDR
        call print_str
        ld hl,FT_INIT           ; "FT 0000000"
        ld de,ft_buf
        ld bc,FT_LEN+1
        ldir
        call draw_money
        xor a
        ld (stars),a
        ld (star_fl),a
        ld (post_ph),a
        ld (dash_ph),a
        ld (trabi_f),a
        ld a,$80
        ld (pol_last),a
        call draw_stars
        call draw_trabi
        ld hl,POLPATH
        ld (pol_path),hl
        ld hl,MUSIC
        call play_music
        ld hl,CAP_CHASE
        ld de,760
        call scene_start
.loop:  call tick
        ret c
        ; távoli városkép: 2 képkockánként 1 bájttal balra, felváltva a két fele
        ld a,(frame)
        rrca
        jr c,.odd
        ld hl,VRAM+SKY0*64
        ld b,SKYHALF
        jr .rot
.odd:   ld hl,VRAM+(SKY0+SKYHALF)*64
        ld b,SKYN-SKYHALF
.rot:   call rot_rows
        ; szalagkorlát oszlopai (gyors)
        ld a,(post_ph)
        add a,2
        and 15
        ld (post_ph),a
        ld hl,POSTLINE
        add a,l
        ld l,a
        jr nc,$+3
        inc h
        ld de,VRAM+POST_Y0*64
        ld b,POST_N
.pr:    push bc
        push hl
        call ldi64
        pop hl
        pop bc
        djnz .pr
        ; felezővonal
        ld a,(dash_ph)
        add a,3
        and 31
        ld (dash_ph),a
        ld hl,DASHLINE0
        ld de,VRAM+DASH_Y0*64
        call dash_row
        ld hl,DASHLINE1
        ld de,VRAM+(DASH_Y0+1)*64
        call dash_row
        ld hl,DASHLINE2
        ld de,VRAM+(DASH_Y0+2)*64
        call dash_row
        ; ütemezett munkák
        ld a,(frame)
        and 3
        jr z,.f0
        dec a
        jr z,.f1
        dec a
        jr z,.f2
        ; 3: rendőrautó
        call police_step
        jr .loop
.f0:    call wanted
        jr .loop
.f1:    ld a,(trabi_f)          ; a Trabant rázkódik
        xor 1
        ld (trabi_f),a
        call draw_trabi
        jp .loop
.f2:    call money_step
        jp .loop

dash_row:
        ld a,(dash_ph)
        add a,l
        ld l,a
        jr nc,$+3
        inc h
        jp ldi64

; rot_rows: HL = első sor, B = sorok száma; minden sort 1 bájttal balra forgat
rot_rows:
.r:     push bc
        ld a,(hl)
        ld d,h
        ld e,l
        inc hl
        call ldi63
        ld (de),a
        pop bc
        djnz .r
        ret

; ldi64 / ldi63: kibontott LDI-sorozat (BC-t rontja)
ldi64:  ldi
ldi63:
        REPT 23
        ldi
        ENDR
ldi40:
        REPT 40
        ldi
        ENDR
        ret

draw_trabi:
        ld hl,TRABI0
        ld a,(trabi_f)
        or a
        jr z,$+5
        ld hl,TRABI1
        ld de,VRAM+CAR_Y*64+TRABI_X
        ld bc,TRABI_W*256+CAR_H
        jp blit_w

; police_step: a rendőrautó helye a POLPATH szerint, a tetőfény villog
police_step:
        ld hl,(frame)
        srl h
        rr l
        srl h
        rr l
        ld a,h
        or a
        jr z,$+4
        ld l,255
        ld h,0
        ld de,(pol_path)
        add hl,de
        ld a,(hl)               ; x (előjeles)
        ld c,a
        ld a,(frame)
        and 8
        ld hl,POLICE0
        jr z,$+5
        ld hl,POLICE1
        ld a,c
        ; balról beúszik: vágás
        ld b,POLICE_W
        bit 7,a
        jr z,.pos
        neg
        cp b
        ret nc
        ld e,a
        ld d,0
        add hl,de
        ld a,b
        sub e
        ld b,a
        xor a
.pos:   push hl
        ld hl,VRAM+CAR_Y*64
        add a,l
        ld l,a
        jr nc,$+3
        inc h
        ex de,hl
        pop hl
        push hl
        ld hl,POLICE_W
        ld (bl_stride),hl
        pop hl
        ld c,CAR_H
        call blit
        ; sziréna, amikor megjelenik
        ld a,(siren_on)
        or a
        ret nz
        inc a
        ld (siren_on),a
        ld hl,SIREN
        jp play_music

; wanted: körözési szint (csillagok) az idővonal szerint, villogással
wanted:
        ld hl,(frame)
        ld de,WANTED_T
        ld a,(stars)
        add a,a
        add a,e
        ld e,a
        jr nc,$+3
        inc d
        ex de,hl
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a                  ; a következő csillag ideje
        ex de,hl
        or a
        sbc hl,de
        jr c,.fl
        ld hl,stars
        inc (hl)
        ld a,24
        ld (star_fl),a
        ld hl,BLIP
        ld a,(siren_on)
        or a
        call z,play_once
.fl:    ld a,(star_fl)
        or a
        ret z
        dec a
        ld (star_fl),a
        ; tovább: draw_stars
draw_stars:
        ld de,HUD_STAR_ADDR
        ld b,0
.s:     push bc
        ld hl,NIB_7_1           ; üres csillag: szürke
        ld a,(stars)
        cp b
        jr z,.p                 ; b >= stars: üres
        jr c,.p
        ld hl,NIB_14_1
        ld a,(star_fl)
        and 2
        jr z,.p
        ld hl,NIB_15_1
.p:     ld (cur_nib),hl
        ld a,G_STAR
        call print_glyph
        pop bc
        inc b
        ld a,b
        cp 5
        jr c,.s
        ret

; money_step: a "zsákmány" számlálója nő
money_step:
        ld hl,ft_buf+FT_LEN-2   ; tízesek
.c:     ld a,(hl)
        inc a
        cp G_0+10
        jr c,.ok
        ld (hl),G_0
        dec hl
        jr .c
.ok:    ld (hl),a
draw_money:
        ld hl,NIB_12_1
        ld (cur_nib),hl
        ld hl,ft_buf
        ld de,HUD_FT_ADDR
        jp print_str

;=============================================================================
; 2b. KOMP TIHANYBA
;=============================================================================
scene_ferry:
        ld hl,IMG_FERRY
        call show_img
        xor a
        ld (siren_on),a
        ld (wave_ph),a
        ld a,4
        ld (ferry_x),a
        ld a,1
        ld (ferry_cnt),a
        ld a,50
        ld (g1x),a
        ld a,27
        ld (g2x),a
        call draw_ferry
        ld hl,FPOLPATH
        ld (pol_path),hl
        ld hl,HORN
        call play_once
        ld hl,CAP_FERRY
        ld de,800
        call scene_start
.loop:  call tick
        ret c
        call ferry_waves
        ld a,(frame)
        and 3
        jr z,.f0
        dec a
        jr z,.f1
        dec a
        jr z,.f2
        call police_step
        jr .loop
.f0:    ld hl,g1x
        ld de,VRAM+38*64
        call gull_one
        ld hl,g2x
        ld de,VRAM+52*64
        call gull_one
        jr .loop
.f1:    ld hl,ferry_cnt         ; a komp 20 képkockánként 1 bájtot halad
        dec (hl)
        jr nz,.loop
        ld (hl),5
        ld hl,(frame)
        ld de,60
        or a
        sbc hl,de
        jr c,.loop
        ld a,(ferry_x)
        cp 24
        jr nc,.loop
        inc a
        ld (ferry_x),a
        call draw_ferry
        jr .loop
.f2:    ld hl,(frame)           ; a sziréna után zene
        ld de,450
        or a
        sbc hl,de
        jr nz,.loop
        ld hl,MUSIC
        call play_music
        jr .loop

draw_ferry:
        ld a,(ferry_x)
        ld hl,VRAM+FERRY_Y*64
        add a,l
        ld l,a
        jr nc,$+3
        inc h
        ex de,hl
        ld hl,FERRY
        ld bc,FERRY_W*256+FERRY_H
        jp blit_w

; ferry_waves: 2 képkockánként a hullámsorok mintáját egy bájttal elcsúsztatja
ferry_waves:
        ld a,(frame)
        and 1
        ret nz
        ld a,(wave_ph)
        inc a
        and 15
        ld (wave_ph),a
        ld hl,FWAVE_TAB
        ld b,FWAVE_N
.w:     push bc
        ld e,(hl) : inc hl : ld d,(hl) : inc hl     ; minta
        ld c,(hl) : inc hl : ld b,(hl) : inc hl     ; képernyőcím
        ld a,(hl) : inc hl : inc hl                 ; csak a rámpától jobbra?
        ld (fw_r),a
        ld a,(hl) : inc hl : inc hl                 ; fáziseltolás
        push hl
        ld l,a
        ld a,(wave_ph)
        add a,l
        and 15
        ld l,a
        ld h,0
        add hl,de
        ld a,(fw_r)
        or a
        ld d,b
        ld e,c
        jr z,.full
        ld bc,RAMP_W
        add hl,bc
        call ldi40
        jr .nx
.full:  call ldi64
.nx:    pop hl
        pop bc
        djnz .w
        ret

; gull_one: HL = a sirály x-változója, DE = a sor címe; balra repül, a szélen újrakezdi
gull_one:
        ld a,(hl)
        or a
        jr nz,.mv
        push hl
        push de
        ex de,hl
        ld a,SKY_GULL_B
        ld bc,GULL_W*256+GULL_H
        call fill_rect
        pop de
        pop hl
        ld a,60
.mv:    dec a
        ld (hl),a
        add a,e
        ld e,a
        jr nc,$+3
        inc d
        ld a,(frame)
        and 8
        ld hl,GULL0
        jr z,$+5
        ld hl,GULL1
        ld bc,GULL_W*256+GULL_H
        jp blit_w

;=============================================================================
; 3. CÍMKÉP
;=============================================================================
scene_title:
        ld hl,IMG_TITLE
        call show_img
        ld hl,FANFARE           ; fanfár, utána a zene
        ld (snd_ptr),hl
        ld hl,MUSIC
        ld (snd_loop),hl
        call snd_next
        ld a,1
        ld (sign_st),a
        ld hl,CAP_TITLE
        ld de,420
        call scene_start
.loop:  call tick
        ret c
        ld a,(frame)            ; a felirat 12 képkockánként villan az elején
        ld b,1
        ld hl,(frame)
        ld de,96
        or a
        sbc hl,de
        jr nc,.set
        ld a,(frame)
        and 8
        jr z,.set
        dec b
.set:   ld a,b
        ld hl,sign_st
        cp (hl)
        jr z,.loop
        ld (hl),a
        ld hl,SUB_OFF
        or a
        jr z,$+5
        ld hl,SUB_ON
        ld de,SUB_ADDR
        ld bc,64*256+13
        call blit_w
        jr .loop

;=============================================================================
; 4. MEGJELENÉS: ...
;=============================================================================
scene_delay:
        call snd_stop
        call cls_all
        ld hl,CAP_NONE
        ld de,1100
        call scene_start
        ld b,25
        call wait
        ret c
        ld hl,DELAY_TAB
        ld b,DELAY_N
.line:  push bc
        push hl
        ld e,(hl) : inc hl : ld d,(hl) : inc hl     ; szöveg
        push de
        ld e,(hl) : inc hl : ld d,(hl) : inc hl     ; cím
        ld a,(hl) : inc hl : inc hl                 ; jelzők
        ld (dl_flags),a
        ld c,(hl) : inc hl : ld b,(hl) : inc hl     ; színtábla
        ld (cur_nib),bc
        ld (cur_big),bc
        ld c,(hl) : inc hl : ld b,(hl) : inc hl     ; áthúzás címe
        ld (dl_strike),bc
        ld a,(hl)
        ld (dl_w),a
        pop hl
        ld a,(dl_flags)
        rrca
        jr nc,.small
        call print_big_str
        jr .printed
.small: call print_str
.printed:
        ld hl,BLIP
        call play_once
        ld a,(dl_flags)
        and 2
        jr z,.nostrike
        ld b,30
        call wait
        jp c,.quit
        ld hl,(dl_strike)
        ld a,(dl_w)
        ld b,a
        ld c,2
        ld a,STRIKE_B
        call fill_rect
        ld hl,STRIKE
        call play_once
.nostrike:
        ld b,40
        call wait
        jr c,.quit
        pop hl
        ld de,12
        add hl,de
        pop bc
        djnz .line
        ; utolsó sor villog, lábjegyzet, majd felhívás
        ld hl,TADA
        call play_once
        ld hl,NIB_7_0
        ld (cur_nib),hl
        ld hl,FOOT1_STR
        ld de,FOOT1_ADDR
        call print_str
.fl:    call tick
        ret c
        ld hl,(frame)
        ld de,DELAY_FOOT2
        or a
        sbc hl,de
        jr nz,.nf
        ld hl,VRAM+226*64
        ld b,64
        ld c,12
        xor a
        call fill_rect
        ld hl,NIB_15_0
        ld (cur_nib),hl
        ld hl,FOOT2_STR
        ld de,FOOT2_ADDR
        call print_str
.nf:    ld a,(frame)
        and 7
        jr nz,.fl
        ld hl,BIG_12_0
        ld a,(frame)
        and 8
        jr z,$+5
        ld hl,BIG_14_0
        ld (cur_big),hl
        ld hl,(DELAY_TAB+(DELAY_N-1)*12)
        ld de,(DELAY_TAB+(DELAY_N-1)*12+2)
        call print_big_str
        jr .fl
.quit:  pop hl
        pop bc
        ret

;=============================================================================
; RENDSZER: képkocka, billentyűzet, kilépés, hang (a korábbi TVC-játékokból)
;=============================================================================
vsync:
        ld hl,3000
.w:     in a,($59)
        and $10
        jr z,.got
        dec hl
        ld a,h
        or l
        jr nz,.w
.got:   out ($07),a
        ret

; read_keys: keys+1: b2 = szóköz/tűz, b3 = Esc; knew = új lenyomások
read_keys:
        ld hl,(keys)
        ld (kprev),hl
        ld de,0
        ld a,8 : out ($03),a : in a,($58) : cpl
        bit 3,a : jr z,$+4 : set 2,d            ; joystick tűz
        ld c,a
        ld a,7 : out ($03),a : in a,($58) : cpl
        ld c,a
        bit 3,c : jr z,$+4 : set 3,d            ; Esc
        bit 5,c : jr z,$+4 : set 2,d            ; szóköz
        ld (keys),de
        ld hl,(kprev)
        ld a,l : cpl : and e : ld (knew),a
        ld a,h : cpl : and d : ld (knew+1),a
        ret

quit:
        call snd_stop
.rel:   call vsync
        call read_keys
        ld hl,(keys)
        ld a,h
        or l
        jr nz,.rel
        call cls_all
        ld a,$70
        ld (P_SAVE),a
        out ($02),a
        ld a,(PORT06) : out ($06),a
        ld a,(PORT05) : out ($05),a
        ld a,(PORT03) : out ($03),a
        ld a,(BORDERV) : out ($00),a
        ld a,(PAPERV) : and 3 : add a,$60 : ld c,a
        xor a
        out (c),a
        ld a,(INKV) : and 3 : add a,$60 : ld c,a
        ld a,$55
        out (c),a
        out ($07),a
quit_sp:
        ld sp,0                 ; önmódosító: BASIC verem
        ei
        rst $30
        db $05                  ; CLS
        ret

; HANG: egycsatornás hanggenerátor, képkockánként léptetett sorozat:
; (db képkocka, hangmagasság alsó/felső, hangerő)*, 0 a vége. snd_loop <> 0: ismétlés onnan
play_music:
        ld (snd_ptr),hl
        ld (snd_loop),hl
        jr snd_next
play_once:
        ld (snd_ptr),hl
        ld hl,0
        ld (snd_loop),hl
        jr snd_next

snd_tick:
        ld a,(snd_ptr+1)
        or a
        ret z
        ld hl,snd_cnt
        dec (hl)
        ret nz
snd_next:
        ld hl,(snd_ptr)
        ld a,(hl)
        or a
        jr nz,.go
        ld hl,(snd_loop)
        ld a,h
        or l
        jr z,snd_stop
        ld a,(hl)
.go:    ld (snd_cnt),a
        inc hl
        ld a,(hl)
        out ($04),a
        inc hl
        ld a,(hl)
        or $10
        out ($05),a
        inc hl
        ld a,(hl)
        add a,a
        add a,a
        or 2                    ; hangerő + 16 színű mód
        out ($06),a
        inc hl
        ld (snd_ptr),hl
        ret

snd_stop:
        xor a
        out ($05),a
        ld (siren_on),a
        ld a,2
        out ($06),a
        ld hl,0
        ld (snd_ptr),hl
        ret

;=============================================================================
; ADATOK
;=============================================================================
CAP_NONE:   dw $FFFF
WANTED_T:   dw 190,270,350,430,510,$FFFF
DELAY_FOOT2 equ 600
FT_LEN      equ 10
FT_INIT:    db G_F,G_T,G_SPACE,G_0,G_0,G_0,G_0,G_0,G_0,G_0,$FF

        include "data.inc"

CODE_END:
        ASSERT CODE_END <= $8000

;=============================================================================
; VÁLTOZÓK (U3)
;=============================================================================
        ORG $C000
BSS:
frame:      dw 0
scene_len:  dw 0
cap_ptr:    dw 0
tw_on:      db 0
tw_cnt:     db 0
tw_src:     dw 0
tw_dst:     dw 0
tw_nib:     dw 0
cur_nib:    dw 0
cur_big:    dw 0
bl_stride:  dw 0
ur_left:    dw 0
keys:       dw 0
kprev:      dw 0
knew:       dw 0
snd_ptr:    dw 0
snd_loop:   dw 0
snd_cnt:    db 0
siren_on:   db 0
sun_y:      db 0
sun_cnt:    db 0
sign_st:    db 0
ds_y:       db 0
ds_addr:    dw 0
ds_tab:     dw 0
rf_w:       dw 0
rf_addr:    dw 0
rf_t:       db 0
stars:      db 0
star_fl:    db 0
post_ph:    db 0
dash_ph:    db 0
trabi_f:    db 0
pol_last:   db 0
ft_buf:     ds FT_LEN+1
pol_path:   dw 0
ferry_x:    db 0
ferry_cnt:  db 0
wave_ph:    db 0
g1x:        db 0
g2x:        db 0
fw_r:       db 0
dl_flags:   db 0
dl_strike:  dw 0
dl_w:       db 0
BSS_LEN     equ $-BSS

        SAVEBIN "gtt6.bin",$19EF,CODE_END-$19EF
