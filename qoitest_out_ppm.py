#打开文件
'''
import os
os.chdir('$LIB$')
'''
f=open("test.qoi",'rb')
output=open("test.ppm",'wb')
'''
out=open('test.rgb','wb')
out.write(b'128 160\n')
'''
'''
import tft
tft.setarea([0,0],[128,160])
'''
#解码配置设置
bytemin=8#加载的最少字节数(8,不要改,除非QOI规范变了)，如果低于该值则继续读文件
loadstep=384#每次加载和写入多少字节，内存够的可以改大
cachesize=512#解码后的缓存，超出该值则进行写入后删除，内存够的可以改大
'''
cache565=b''#16位色缓存
'''
pos=-1
#检测文件头
if f.read(4)!=b'qoif':
    f.close()
    del f
    print('不是一个有效的QOI文件')
else:
    #获取图像信息
    w=f.read(4)
    width=(w[0]<<24)+(w[1]<<16)+(w[2]<<8)+w[3]
    del w
    h=f.read(4)
    height=(h[0]<<24)+(h[1]<<16)+(h[2]<<8)+h[3]
    del h
    channels=f.read(1)[0]
    colorspace=f.read(1)[0]#这玩意干啥的？？
    print(width,height,channels)
    channels=3#由于是PPM,强制RGB格式
    #PPM文件头
    output.write(b'P6\n')
    output.write(bytes(str(width),encoding='ascii')+b' '+bytes(str(height),encoding='ascii')+b'\n255\n')
    
    #创建index
    index=bytearray(64*channels)
    
    #开始图像数据解码
    byte=bytearray(f.read(loadstep))
    cache=b''
    
    while byte:
        
        byte+=bytearray(f.read(loadstep))
        
        while len(byte)>bytemin:
            pos+=1
            if byte[0]==0b11111110:#RGB
                cache+=byte[1:4]
                if channels==4:cache+=b'\xff'
                byte=byte[4:]
                #input('Detected RGB')
                
            elif byte[0]==0b11111111:#RGBA
                cache+=byte[1:5]
                byte=byte[5:]
                #input('Detected RGBA')
                
            elif (byte[0]>>6)==0:#INDEX
                indexp=byte[0]&0b00111111
                cache+=index[indexp*channels:(1+indexp)*channels]
                #del byte[0]
                byte=byte[1:]
                #input('Detected INDEX')
                
            elif (byte[0]>>6)==1:#DIFF
                #indexp=len(cache)-channels-1
                cache+=bytes([(cache[-channels] + (byte[0]>>4)%4-2) %256])
                cache+=bytes([(cache[-channels] + (byte[0]>>2)%4-2) %256])
                cache+=bytes([(cache[-channels] + byte[0]%4-2) %256])
                if channels==4:cache+=bytes([cache[-channels]])
                #del byte[0]
                byte=byte[1:]
                #input('Detected DIFF')
                
            elif (byte[0]>>6)==2:#LUMA
                #indexp=len(cache)-channels-1
                dg=byte[0]%64-32
                dr,db=(byte[1]>>4)+dg-8,(byte[1]%16)+dg-8
                cache+=bytes([(cache[-channels] + dr) %256])
                cache+=bytes([(cache[-channels] + dg) %256])
                cache+=bytes([(cache[-channels] + db) %256])
                if channels==4:cache+=bytes([cache[-channels]])
                #del byte[0:2]
                del dr,dg,db
                byte=byte[2:]
                #input('Detected LUMA')
                
            elif (byte[0]>>6)==3:#RUN
                for i in range(byte[0]%64+1):
                    cache+=cache[-channels:] if cache[-channels:] else b'\x00\x00\x00'
                #del byte[0]
                pos+=byte[0]%64
                
                byte=byte[1:]
                
                #input('Detected RUN')
                
            #写入INDEX
            if channels==3:
                indexp=(cache[-3]*3+cache[-2]*5+cache[-1]*7+255*11)%64
                index[indexp*3:indexp*3+3]=cache[-3:]
            elif channels==4:
                indexp=(cache[-4]*3+cache[-3]*5+cache[-2]*7+cache[-1]*11)%64
                index[indexp*channels:indexp*channels+4]=cache[-4:]
                
            #print(cache[-3],cache[-2],cache[-1],len(cache),[pos//128,pos%128],'\n')
            
            #满缓存
            if len(cache)>cachesize:
                '''
                buf=bytearray(2)
                for i in range(len(cache)//channels):
                    buf[0]=(cache[i*channels]>>3<<3)+(cache[i*channels+1]>>5)
                    buf[1]=( ((cache[i*channels+1]>>2)&0b000111) + (cache[i*channels+2]>>3))
                    cache565+=buf
                '''
                output.write(cache[:loadstep])
                cache=cache[loadstep:]
                '''
                out.write(cache565)
                cache565=b''
                '''
             
            #解码完毕
            if len(byte)==8 and byte==b'\x00\x00\x00\x00\x00\x00\x00\x01':
                '''
                buf=bytearray(2)
                for i in range(len(cache)//channels):
                    buf[0]=(cache[i*channels]>>3<<3)+(cache[i*channels+1]>>5)
                    buf[1]=( ((cache[i*channels+1]>>2)&0b000111) + (cache[i*channels+2]>>3))
                    cache565+=buf
                out.write(cache565)
                del cache,cache565
                byte=b''
                out.close()
                '''
                output.write(cache)
                f.close()
                output.close()
                byte=b''
                del cache#,cache565