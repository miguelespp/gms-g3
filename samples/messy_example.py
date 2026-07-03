import os,sys,re,json,math,random,time,datetime,collections,itertools
def proc(d,t,f,x,y,z,w,v,u,q,r,s,p,o,n,m,l,k,j,i,h,g,e,b,a,c):
 if d==1:
  if t==2:
   if f==3:
    if x==4:
     if y==5:
      if z==6:
       if w==7:
        if v==8:
         result=a+b+c+d+e+f+g+h+i+j+k+l+m+n+o+p+q+r+s+t+u+v+w+x+y+z
         return result
        elif v==9:
         for idx in range(0,100):
          if idx%2==0:
           if idx%3==0:
            if idx%5==0:
             result=idx*a+b-c
             return result
            elif idx%7==0:
             result=idx/a if a!=0 else 0
             return result
            else:
             result=idx
         return -1
        else:
         while True:
          if random.random()>0.99:
           break
         return 0
       else:
        lst=[]
        for i2 in range(100):
         for j2 in range(100):
          for k2 in range(100):
           lst.append(i2*j2*k2)
        return sum(lst)
      else:
       return z*y*x*w*v*u*q*r*s*p*o*n*m*l*k*j*i*h*g*e*b*a*c
     else:
      return y-x+w-v+u-q+r-s+p-o+n-m+l-k+j-i+h-g+e-b+a-c
    else:
     return x**2+y**2+z**2+w**2+v**2+u**2+q**2+r**2+s**2+p**2
   else:
    return f*t+d*x+y*z+w*v+u*q+r*s+p*o+n*m+l*k+j*i+h*g+e*b+a*c
  else:
   return t-d+f-x+y-z+w-v+u-q+r-s+p-o+n-m+l-k+j-i+h-g+e-b+a-c
 else:
  return d+t+f+x+y+z+w+v+u+q+r+s+p+o+n+m+l+k+j+i+h+g+e+b+a+c
def f2(L):
 r=[]
 for x in L:
  if x>0:
   if x%2==0:
    if x%3==0:
     r.append(x*3)
    elif x%5==0:
     r.append(x*5)
    else:
     r.append(x*2)
   elif x%7==0:
    r.append(x*7)
   else:
    r.append(x)
  elif x<0:
   if x%2!=0:
    r.append(-x)
   else:
    r.append(x*x)
  else:
   r.append(0)
 return r
def f3(s):
 o="";c=0
 for ch in s:
  if ch.isalpha():
   if ch.isupper():
    o+=ch.lower();c+=1
   elif ch.islower():
    o+=ch.upper();c+=1
   else:
    o+=ch
  elif ch.isdigit():
   o+=str(int(ch)*2 if int(ch)<5 else int(ch)-1)
  else:
   o+=ch
 return o,c
MAGIC1=42;MAGIC2=137;MAGIC3=9999;MAGIC4=0.00001;MAGIC5=3.14159265
def compute(a,b):
 return (a*MAGIC1+b*MAGIC2)%(MAGIC3) if (a+b)!=0 else MAGIC4*MAGIC5
